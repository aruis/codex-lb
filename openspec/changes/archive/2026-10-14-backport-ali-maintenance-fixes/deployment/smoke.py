"""Run inside codex-lb: two tiny authenticated requests with an expiring temporary key."""

import asyncio
import json
import time
import urllib.request
from datetime import timedelta

from app.core.utils.time import utcnow
from app.db.session import SessionLocal, close_db
from app.modules.api_keys.repository import ApiKeysRepository
from app.modules.api_keys.service import ApiKeyCreateData, ApiKeysService


def request(key, history):
    payload = {
        "model": "gpt-6-luna",
        "instructions": "For this connectivity check, answer with the single word OK.",
        "input": history,
        "stream": True,
        "store": False,
        "reasoning": {"effort": "low"},
        "prompt_cache_key": "ali-stable-patch-smoke-20261014-maintenance",
    }
    headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "originator": "codex_cli_rs",
        "version": "0.162.1",
        "User-Agent": "codex_cli_rs/0.162.1",
        "session-id": "ali-stable-patch-smoke-20261014-maintenance",
    }
    req = urllib.request.Request(
        "http://127.0.0.1:2455/backend-api/codex/responses",
        data=json.dumps(payload).encode(),
        headers=headers,
    )
    started = time.monotonic()
    completed = False
    text = ""
    error = None
    with urllib.request.urlopen(req, timeout=45) as response:
        for raw in response:
            if time.monotonic() - started > 90:
                raise TimeoutError("Smoke request exceeded its total budget")
            line = raw.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            event = json.loads(line[6:])
            if event.get("type") == "response.output_text.delta":
                text += event.get("delta", "")
            if event.get("type") == "response.completed":
                completed = True
                break
            if event.get("type") in {"response.failed", "error"}:
                details = event.get("error") or event.get("response", {}).get("error", {})
                error = details.get("code", "unknown")
                break
        result = {
            "http_status": response.status,
            "completed": completed,
            "reply_is_ok": text.strip().rstrip(".") == "OK",
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "error_code": error,
        }
    print("SMOKE_RESULT", json.dumps(result), flush=True)
    if not completed or error:
        raise RuntimeError("Authenticated smoke request did not complete")


async def main():
    created = None
    try:
        async with SessionLocal() as session:
            service = ApiKeysService(ApiKeysRepository(session))
            created = await service.create_key(
                ApiKeyCreateData(
                    name="temporary-ali-patch-smoke-20261014-maintenance",
                    allowed_models=["gpt-6-luna"],
                    expires_at=utcnow() + timedelta(minutes=5),
                    transport_policy_override="always_websocket",
                )
            )
        history = [{"role": "user", "content": [{"type": "input_text", "text": "Connectivity check: reply OK."}]}]
        await asyncio.to_thread(request, created.key, history)
        history += [
            {"role": "assistant", "content": [{"type": "output_text", "text": "OK"}]},
            {"role": "user", "content": [{"type": "input_text", "text": "Repeat your previous answer."}]},
        ]
        await asyncio.to_thread(request, created.key, history)
    finally:
        if created is not None:
            async with SessionLocal() as session:
                await ApiKeysService(ApiKeysRepository(session)).delete_key(created.id)
            print("TEMPORARY_KEY_REMOVED", flush=True)
        await close_db()


asyncio.run(main())
