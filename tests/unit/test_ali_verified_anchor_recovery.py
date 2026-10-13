"""Stable recovery sends verified history once and never changes account ownership."""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from app.core.clients.proxy import ProxyResponseError
from app.modules.proxy import service as proxy_service
from tests.unit.test_proxy_http_bridge import _make_app_settings, _make_bridge_session

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    [
        "verified",
        "rewritten",
        "unverified",
        "visible",
        "accepted",
        "replayed",
        "retry_failure",
        "operation",
        "fence_failure",
    ],
)
async def test_verified_anchor_recovery_preserves_history_and_owner(monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    service = proxy_service.ProxyService(cast(Any, nullcontext()))
    history = [
        {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "remember blue"}]},
        {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "blue"}]},
        {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "what color?"}]},
    ]
    fresh = {"model": "gpt-5.6-sol", "instructions": "retain context", "input": history}
    payload = proxy_service.ResponsesRequest.model_validate({**fresh, "previous_response_id": "resp_stale"})
    initial = _make_bridge_session(key_value="ali-anchor")
    replacement = _make_bridge_session(key_value="ali-anchor")
    state = proxy_service._WebSocketRequestState(
        request_id="req-ali-anchor",
        model=payload.model,
        service_tier=None,
        reasoning_effort=None,
        api_key_reservation=None,
        started_at=time.monotonic(),
        event_queue=asyncio.Queue(),
        transport="http",
        previous_response_id="resp_stale",
        preferred_account_id=initial.account.id,
        fresh_upstream_request_is_retry_safe=case != "unverified",
        fresh_upstream_request_text=json.dumps({"type": "response.create", **fresh}),
        downstream_visible=case == "visible",
        response_id="resp_started" if case == "accepted" else None,
        response_event_count=1 if case == "accepted" else 0,
        replay_count=1 if case == "replayed" else 0,
        previous_response_not_found_rewritten=case == "rewritten",
    )
    if case in {"operation", "fence_failure"}:
        initial.durable_session_id = "bridge-ali"
        initial.durable_owner_epoch = 3
        state.operation_registered = True
        state.operation_id = "op-ali"
        state.operation_fingerprint = "fingerprint-ali"

    prepared: list[proxy_service.ResponsesRequest] = []
    states: list[proxy_service._WebSocketRequestState] = []

    def prepare(
        prepared_payload: proxy_service.ResponsesRequest, _headers: Any, **_kwargs: Any
    ) -> tuple[proxy_service._WebSocketRequestState, str]:
        prepared.append(prepared_payload)
        if len(prepared) == 1:
            request_state = state
        else:
            request_state = proxy_service._WebSocketRequestState(
                request_id="req-ali-retry",
                model=payload.model,
                service_tier=None,
                reasoning_effort=None,
                api_key_reservation=None,
                started_at=state.started_at,
                event_queue=asyncio.Queue(),
                transport="http",
                previous_response_id=prepared_payload.previous_response_id,
            )
        states.append(request_state)
        return request_state, json.dumps({"type": "response.create", **prepared_payload.to_payload()})

    ordering: list[str] = []

    async def reset_spool(**_kwargs: Any) -> bool:
        ordering.append("spool")
        return case != "fence_failure"

    async def close(_session: Any, **_kwargs: Any) -> None:
        ordering.append("close")

    completed = 'data: {"type":"response.completed","response":{"id":"resp_recovered"}}\n\n'
    wire_bodies: list[dict[str, Any]] = []

    async def stream(_session: Any, *, text_data: str, **_kwargs: Any):
        body = json.loads(text_data)
        wire_bodies.append(body)
        if len(wire_bodies) == 1 or body.get("previous_response_id") or case == "retry_failure":
            code = "bridge_previous_response_not_found" if case == "rewritten" else "previous_response_not_found"
            raise ProxyResponseError(400, proxy_service.openai_error(code, "Previous response was not found."))
        yield completed

    get_session = AsyncMock(side_effect=[initial, replacement])
    monkeypatch.setattr(proxy_service, "get_settings", _make_app_settings)
    monkeypatch.setattr(
        proxy_service,
        "get_settings_cache",
        lambda: SimpleNamespace(
            get=AsyncMock(
                return_value=SimpleNamespace(
                    sticky_threads_enabled=False,
                    openai_cache_affinity_max_age_seconds=1800,
                    http_responses_session_bridge_prompt_cache_idle_ttl_seconds=3600,
                    http_responses_session_bridge_gateway_safe_mode=False,
                )
            )
        ),
    )
    monkeypatch.setattr(service._durable_bridge, "lookup_request_targets", AsyncMock(return_value=None))
    monkeypatch.setattr(service._durable_bridge, "reset_operation_event_spool", AsyncMock(side_effect=reset_spool))
    monkeypatch.setattr(
        service, "_resolve_websocket_previous_response_owner", AsyncMock(return_value=initial.account.id)
    )
    monkeypatch.setattr(service, "_resolve_file_account_for_responses", AsyncMock(return_value=None))
    monkeypatch.setattr(service, "_prepare_http_bridge_request", prepare)
    monkeypatch.setattr(service, "_get_or_create_http_bridge_session", get_session)
    monkeypatch.setattr(service, "_stream_http_bridge_session_events", stream)
    monkeypatch.setattr(service, "_close_http_bridge_session", AsyncMock(side_effect=close))

    async def collect() -> list[str]:
        return [
            chunk
            async for chunk in service._stream_via_http_bridge(
                payload,
                headers={},
                codex_session_affinity=False,
                propagate_http_errors=True,
                openai_cache_affinity=True,
                api_key=None,
                api_key_reservation=None,
                suppress_text_done_events=False,
                idle_ttl_seconds=120.0,
                codex_idle_ttl_seconds=1800.0,
                max_sessions=8,
                queue_limit=4,
            )
        ]

    safe = case in {"verified", "rewritten", "retry_failure", "operation", "fence_failure"}
    if case in {"verified", "rewritten", "operation"}:
        assert await collect() == [completed]
    else:
        with pytest.raises(ProxyResponseError) as caught:
            await collect()
        if case == "fence_failure":
            assert caught.value.payload["error"]["code"] == "bridge_continuity_persistence_failed"
            assert ordering == ["spool"]
            assert len(wire_bodies) == 1
            return

    assert len(wire_bodies) == 2
    if safe:
        assert not wire_bodies[1].get("previous_response_id")
        assert wire_bodies[1]["input"] == history
        assert wire_bodies[1]["instructions"] == "retain context"
        retry = get_session.await_args_list[-1]
        assert retry.kwargs["preferred_account_id"] == initial.account.id
        assert retry.kwargs["fallback_on_preferred_account_unavailable"] is False
        assert retry.kwargs["durable_lookup"] is None
        assert retry.kwargs["request_deadline"] == get_session.await_args_list[0].kwargs["request_deadline"]
        assert states[-1].replay_count == 1
    else:
        assert wire_bodies[1]["previous_response_id"] == "resp_stale"
    if case == "operation":
        assert ordering[:2] == ["spool", "close"]
        assert states[-1].operation_id == "op-ali"
        assert states[-1].operation_rebind_required is True
