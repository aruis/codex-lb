"""Execute in the deployed container: real probe and read-only dashboard parity."""

import asyncio
import json
import math
import time
from unittest.mock import patch

from app.core.clients.http import close_http_client, init_http_client
from app.core.utils.time import utcnow
from app.db.session import SessionLocal, close_db
from app.dependencies import get_accounts_context
from app.modules.accounts.repository import AccountsRepository
from app.modules.dashboard import service as dashboard_module
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.service import DashboardService


def equal(left, right):
    if isinstance(right, dict):
        return (
            isinstance(left, dict) and left.keys() == right.keys() and all(equal(left[k], v) for k, v in right.items())
        )
    if isinstance(right, list):
        return isinstance(left, list) and len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    if isinstance(right, float):
        return isinstance(left, (int, float)) and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)
    return left == right


async def main():
    try:
        await init_http_client()
        async with SessionLocal() as session:
            accounts = await AccountsRepository(session).list_accounts()
            candidates = [a for a in accounts if a.status.value == "active" and a.plan_type == "pro"]
            if len(candidates) != 1:
                raise RuntimeError("Expected one active Pro account for bounded smoke validation")
            started = time.monotonic()
            result = await get_accounts_context(session).service.probe_account(candidates[0].id, model="gpt-6-luna")
            if result is None:
                raise RuntimeError("Probe account disappeared")
            print(
                "LIVE_PROBE",
                json.dumps(
                    {
                        "http_status": result.probe_status_code,
                        "status_before": result.account_status_before,
                        "status_after": result.account_status_after,
                        "usage_refresh_fetch_succeeded": result.usage_refresh_ready_for_probe_settlement(),
                        "elapsed_seconds": round(time.monotonic() - started, 2),
                    }
                ),
                flush=True,
            )
            if result.probe_status_code != 200 or result.account_status_after != "active":
                raise RuntimeError("Live Force Probe did not pass")
        fixed_now = utcnow()
        original_cap = dashboard_module._PROJECTION_HISTORY_PER_ACCOUNT_ROW_CAP
        original_fetch = DashboardRepository.bulk_usage_history_since
        reads = []

        async def recording_fetch(self, *args, **kwargs):
            rows = await original_fetch(self, *args, **kwargs)
            reads.append(sum(len(values) for values in rows.values()))
            return rows

        with (
            patch.object(dashboard_module, "utcnow", lambda: fixed_now),
            patch.object(DashboardRepository, "bulk_usage_history_since", recording_fetch),
        ):
            async with SessionLocal() as session:
                service = DashboardService(DashboardRepository(session))
                capped = (await service.get_projections()).model_dump(mode="json")
                split = len(reads)
                with patch.object(dashboard_module, "_PROJECTION_HISTORY_PER_ACCOUNT_ROW_CAP", 10**9):
                    uncapped = (await service.get_projections()).model_dump(mode="json")
                matches = equal(capped, uncapped)
                print(
                    "LIVE_DASHBOARD",
                    json.dumps(
                        {
                            "capped_rows": sum(reads[:split]),
                            "uncapped_rows": sum(reads[split:]),
                            "payload_parity": matches,
                            "stable_tail_cap": original_cap,
                        }
                    ),
                    flush=True,
                )
                if not matches:
                    raise RuntimeError("Live dashboard capped/uncapped payload parity failed")
    finally:
        await close_http_client()
        await close_db()


asyncio.run(main())
