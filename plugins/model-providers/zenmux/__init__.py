"""Zenmux provider profile (OpenAI-compatible, free-tier filter)."""

import json
from typing import Any

from providers import register_provider
from providers.base import ProviderProfile, _profile_user_agent


def _zenmux_free_pricing_check(item: dict[str, Any]) -> bool:
    """Return True when the model has zero-cost pricing for prompt+completion.

    Zenmux returns a ``pricings`` object with named tiers. A model counts as
    free when every numeric ``value`` under ``pricings`` equals ``0``.
    Missing or malformed pricing => not considered free.
    """
    pricings = item.get("pricings")
    if not isinstance(pricings, dict) or not pricings:
        return False
    saw_numeric = False
    for tier_val in pricings.values():
        if not isinstance(tier_val, list):
            return False
        for entry in tier_val:
            if not isinstance(entry, dict):
                return False
            value = entry.get("value")
            if value is None:
                continue
            if not isinstance(value, (int, float)):
                return False
            saw_numeric = True
            if float(value) != 0.0:
                return False
    return saw_numeric


class ZenmuxProfile(ProviderProfile):
    """Zenmux — filter live catalog down to free (zero-price) models only."""

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        caller_base = (base_url or "").strip()
        effective_base = caller_base or self.base_url
        custom_base = bool(caller_base) and (
            caller_base.rstrip("/") != (self.base_url or "").rstrip("/")
        )
        if custom_base:
            url = caller_base.rstrip("/") + "/models"
        else:
            url = (self.models_url or "").strip() or (
                effective_base.rstrip("/") + "/models" if effective_base else ""
            )
        if not url:
            return None

        import urllib.request

        from hermes_cli.urllib_security import open_credentialed_url

        req = urllib.request.Request(url)
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", _profile_user_agent())
        for k, v in self.default_headers.items():
            req.add_header(k, v)

        try:
            with open_credentialed_url(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            return None

        items = data.get("data") if isinstance(data, dict) else None
        if not isinstance(items, list):
            return None

        free_ids: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if not isinstance(model_id, str):
                continue
            if _zenmux_free_pricing_check(item):
                free_ids.append(model_id)
        return free_ids or None


zenmux = ZenmuxProfile(
    name="zenmux",
    aliases=("zenmux.ai",),
    env_vars=("ZENMUX_API_KEY",),
    display_name="Zenmux (free models)",
    description="Zenmux multiplex — lists only zero-price models from /models",
    signup_url="https://zenmux.ai",
    base_url="https://zenmux.ai/api/v1",
    fallback_models=(
        "atria-asi/atria-dawn-preview",
        "inclusionai/ling-3.0-flash-vl",
    ),
    supports_vision=False,
)

register_provider(zenmux)
