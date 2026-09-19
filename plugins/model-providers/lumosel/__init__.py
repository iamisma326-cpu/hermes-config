"""Lumosel provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile


lumosel = ProviderProfile(
    name="lumosel",
    aliases=("lumo",),
    env_vars=("LUMOSEL_API_KEY",),
    display_name="Lumosel",
    description="Lumosel — OpenAI-compatible endpoint (Claude, GPT, Grok, Kimi)",
    signup_url="https://api.lumosel.vip",
    fallback_models=(
        "claude-sonnet-5",
        "claude-opus-5",
        "gpt-5.6-sol",
        "grok-4-5",
        "kimi-k3",
    ),
    base_url="https://api.lumosel.vip/v1",
)

register_provider(lumosel)
