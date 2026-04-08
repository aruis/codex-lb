from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.core.config.settings import get_settings
from app.core.openai.requests import ResponsesRequest
from app.modules.api_keys.service import ApiKeyUsageReservationData
from app.modules.proxy.http_bridge_forwarding import (
    HTTP_BRIDGE_CODEX_AFFINITY_HEADER,
    HTTP_BRIDGE_FORWARDED_HEADER,
    HTTP_BRIDGE_ORIGIN_INSTANCE_HEADER,
    HTTP_BRIDGE_RESERVATION_KEY_ID_HEADER,
    HTTP_BRIDGE_RESERVATION_MODEL_HEADER,
    HTTP_BRIDGE_SIGNATURE_HEADER,
    HTTP_BRIDGE_TARGET_INSTANCE_HEADER,
    HTTPBridgeForwardContext,
    _owner_forward_receive_timeout,
    _owner_forward_timeout,
    build_owner_forward_headers,
    parse_forwarded_request,
)


@pytest.fixture(autouse=True)
def _temp_bridge_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    monkeypatch.setenv("CODEX_LB_ENCRYPTION_KEY_FILE", str(tmp_path / "bridge.key"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _payload() -> ResponsesRequest:
    return ResponsesRequest.model_validate({"model": "gpt-5.4", "instructions": "hi", "input": "hi"})


def test_parse_forwarded_request_accepts_signed_internal_forward() -> None:
    payload = _payload()
    context = HTTPBridgeForwardContext(
        origin_instance="instance-a",
        target_instance="instance-b",
        codex_session_affinity=True,
        downstream_turn_state="http_turn_123",
        reservation=ApiKeyUsageReservationData(
            reservation_id="res_123",
            key_id="key_123",
            model="gpt-5.4",
        ),
    )
    headers = build_owner_forward_headers(headers={}, payload=payload, context=context)

    forwarded, error = parse_forwarded_request(
        headers,
        payload=payload,
        current_instance="instance-b",
    )

    assert error is None
    assert forwarded is not None
    assert forwarded.context == context


def test_parse_forwarded_request_rejects_missing_signature() -> None:
    payload = _payload()
    headers = {
        HTTP_BRIDGE_FORWARDED_HEADER: "1",
        HTTP_BRIDGE_ORIGIN_INSTANCE_HEADER: "instance-a",
        HTTP_BRIDGE_TARGET_INSTANCE_HEADER: "instance-b",
        HTTP_BRIDGE_CODEX_AFFINITY_HEADER: "0",
    }

    forwarded, error = parse_forwarded_request(
        headers,
        payload=payload,
        current_instance="instance-b",
    )

    assert forwarded is None
    assert error is not None
    assert error.status_code == 400
    assert error.payload["error"]["code"] == "bridge_forward_invalid"


def test_parse_forwarded_request_rejects_tampered_signature() -> None:
    payload = _payload()
    context = HTTPBridgeForwardContext(
        origin_instance="instance-a",
        target_instance="instance-b",
        codex_session_affinity=False,
        downstream_turn_state=None,
        reservation=ApiKeyUsageReservationData(
            reservation_id="res_123",
            key_id="key_123",
            model="gpt-5.4",
        ),
    )
    headers = build_owner_forward_headers(headers={}, payload=payload, context=context)
    headers[HTTP_BRIDGE_SIGNATURE_HEADER] = "bad-signature"

    forwarded, error = parse_forwarded_request(
        headers,
        payload=payload,
        current_instance="instance-b",
    )

    assert forwarded is None
    assert error is not None
    assert error.status_code == 400
    assert error.payload["error"]["code"] == "bridge_forward_invalid"


def test_parse_forwarded_request_rejects_tampered_reservation_fields() -> None:
    payload = _payload()
    context = HTTPBridgeForwardContext(
        origin_instance="instance-a",
        target_instance="instance-b",
        codex_session_affinity=False,
        downstream_turn_state=None,
        reservation=ApiKeyUsageReservationData(
            reservation_id="res_123",
            key_id="key_123",
            model="gpt-5.4",
        ),
    )
    headers = build_owner_forward_headers(headers={}, payload=payload, context=context)
    headers[HTTP_BRIDGE_RESERVATION_KEY_ID_HEADER] = "key_tampered"
    headers[HTTP_BRIDGE_RESERVATION_MODEL_HEADER] = "gpt-5.5"

    forwarded, error = parse_forwarded_request(
        headers,
        payload=payload,
        current_instance="instance-b",
    )

    assert forwarded is None
    assert error is not None
    assert error.status_code == 400
    assert error.payload["error"]["code"] == "bridge_forward_invalid"


def test_parse_forwarded_request_rejects_wrong_target_as_server_error() -> None:
    payload = _payload()
    context = HTTPBridgeForwardContext(
        origin_instance="instance-a",
        target_instance="instance-b",
        codex_session_affinity=False,
        downstream_turn_state=None,
    )
    headers = build_owner_forward_headers(headers={}, payload=payload, context=context)

    forwarded, error = parse_forwarded_request(
        headers,
        payload=payload,
        current_instance="instance-c",
    )

    assert forwarded is None
    assert error is not None
    assert error.status_code == 503
    assert error.payload["error"]["code"] == "bridge_owner_forward_failed"


def test_owner_forward_timeout_only_bounds_connect_phase() -> None:
    timeout = _owner_forward_timeout(connect_timeout_seconds=8.0, idle_timeout_seconds=300.0)

    assert timeout.total is None
    assert timeout.sock_connect == pytest.approx(8.0)
    assert timeout.sock_read == pytest.approx(300.0)


def test_owner_forward_receive_timeout_prefers_idle_timeout_with_budget_remaining(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.modules.proxy.http_bridge_forwarding.time.monotonic", lambda: 100.0)

    timeout = _owner_forward_receive_timeout(
        request_started_at=10.0,
        proxy_request_budget_seconds=300.0,
        stream_idle_timeout_seconds=45.0,
    )

    assert timeout.timeout_seconds == pytest.approx(45.0)
    assert timeout.error_code == "stream_idle_timeout"


def test_owner_forward_receive_timeout_clamps_to_remaining_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.proxy.http_bridge_forwarding.time.monotonic", lambda: 100.0)

    timeout = _owner_forward_receive_timeout(
        request_started_at=10.0,
        proxy_request_budget_seconds=95.0,
        stream_idle_timeout_seconds=45.0,
    )

    assert timeout.timeout_seconds == pytest.approx(5.0)
    assert timeout.error_code == "upstream_request_timeout"
