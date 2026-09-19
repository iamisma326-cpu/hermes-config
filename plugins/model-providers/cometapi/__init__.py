"""CometAPI provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

cometapi = ProviderProfile(
    name="cometapi",
    aliases=("comet",),
    env_vars=("COMETAPI_API_KEY",),
    display_name="CometAPI",
    description="CometAPI multi-vendor gateway (OpenAI-compatible)",
    signup_url="https://www.cometapi.com/",
    fallback_models=("claude-fable-5-1",),
    base_url="https://api.cometapi.com/v1",
)

register_provider(cometapi)
