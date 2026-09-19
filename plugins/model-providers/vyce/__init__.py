"""VyceAI provider (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

vyce = ProviderProfile(
    name="vyce",
    aliases=("vy",),
    env_vars=("VYCE_API_KEY",),
    display_name="VyceAI",
    description="VyceAI router (vyceai.com) - claude, deepseek, agnes models",
    signup_url="https://vyceai.com/",
    fallback_models=("deepseek-v4-flash", "deepseek-v4.1", "claude-sonnet-4-6"),
    base_url="https://vyceai.com/v1",
)

register_provider(vyce)
