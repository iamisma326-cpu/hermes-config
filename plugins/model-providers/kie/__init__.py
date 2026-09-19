"""Kie.ai Codex provider profile (OpenAI Responses API)."""

from providers import register_provider
from providers.base import ProviderProfile

kie = ProviderProfile(
    name="kie",
    aliases=("kieai",),
    api_mode="codex_responses",
    env_vars=("KIE_API_KEY",),
    display_name="Kie.ai Codex",
    description="Kie.ai Codex gateway (OpenAI Responses API)",
    signup_url="https://kie.ai/",
    fallback_models=("gpt-5-5",),
    base_url="https://api.kie.ai/codex/v1",
)

register_provider(kie)
