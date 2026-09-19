"""KiosAPI router provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

kiosapi = ProviderProfile(
    name="kiosapi",
    aliases=("kios",),
    env_vars=("KIOSAPI_API_KEY",),
    display_name="KiosAPI Router",
    description="KiosAPI model router (OpenAI-compatible, multi-vendor models). NOTE (2026-09-18): router.kiosapi.com DNS does not resolve — defunct/unreachable; verify before relying on it.",
    signup_url="https://kiosapi.com/",
    fallback_models=("kimi-k3",),
    base_url="https://router.kiosapi.com/v1",
    default_headers={"User-Agent": "Hermes-Agent"},
)

register_provider(kiosapi)
