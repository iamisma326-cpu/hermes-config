"""Token Harbor provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

tokenharbor = ProviderProfile(
    name="tokenharbor",
    aliases=("th",),
    env_vars=("TOKENHARBOR_API_KEY",),
    display_name="Token Harbor",
    description="Token Harbor API gateway (OpenAI-compatible, multi-vendor models)",
    signup_url="https://tokenharbor.ai/",
    fallback_models=("deepseek-v4-flash:free",),
    base_url="https://tokenharbor.ai/v1",
)

register_provider(tokenharbor)
