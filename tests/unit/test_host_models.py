from __future__ import annotations

import pytest

from app.core.openai.host_models import resolve_default_host_model
from app.core.openai.model_registry import get_model_registry

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
@pytest.mark.parametrize("authoritative", [False, True])
@pytest.mark.parametrize(
    "catalog, expected",
    [
        (None, "gpt-5.6-luna"),
        (("gpt-5.6-luna", "gpt-5.5"), "gpt-5.6-luna"),
        (("gpt-5.6-luna",), "gpt-5.6-luna"),
        (("gpt-5.5",), "gpt-5.5"),
        ((), "gpt-5.6-luna"),
    ],
)
async def test_default_host_respects_catalog(catalog, expected, authoritative):
    registry = get_model_registry()
    if catalog is not None:
        models = registry.get_models_with_fallback()
        visible = [models[slug] for slug in catalog]
        await registry.update(
            {"pro": visible},
            per_account_results={"account": ("pro", visible)} if authoritative else None,
        )
        if authoritative:
            for slug in ("gpt-5.6-luna", "gpt-5.5"):
                assert registry.is_suppressed_model(slug) == (slug not in catalog)
    assert resolve_default_host_model() == expected
