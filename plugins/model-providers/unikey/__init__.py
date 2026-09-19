"""UniKey provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

unikey = ProviderProfile(
    name="unikey",
    aliases=("uk",),
    env_vars=("UNIKEY_API_KEY",),
    display_name="UniKey",
    description="UniKey multi-vendor API gateway (OpenAI-compatible)",
    signup_url="https://www.getunikey.ai/",
    fallback_models=("deepseek-v4-flash",),
    base_url="https://www.getunikey.ai/v1",
)

register_provider(unikey)
