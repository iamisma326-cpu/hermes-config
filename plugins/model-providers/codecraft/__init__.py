"""CodeCraft API provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

codecraft = ProviderProfile(
    name="codecraft",
    aliases=("cc",),
    env_vars=("CODECRAFT_API_KEY",),
    display_name="CodeCraft API",
    description="CodeCraft multi-vendor gateway (OpenAI-compatible)",
    signup_url="https://codecraftapi.com/",
    fallback_models=("kimi-k3", "glm-5.3", "muse-spark-1.1"),
    base_url="https://codecraftapi.com/v1",
)

register_provider(codecraft)
