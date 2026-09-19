"""TokenRouter provider profile."""

from providers import register_provider
from providers.base import ProviderProfile


tokenrouter = ProviderProfile(
    name="tokenrouter",
    aliases=("token-router",),
    env_vars=("TOKENROUTER_API_KEY",),
    display_name="TokenRouter",
    description="TokenRouter — multi-model OpenAI-compatible router",
    signup_url="https://tokenrouter.com/",
    fallback_models=(
        "qwen/qwen3.7-max",
        "deepseek/deepseek-v4-pro",
        "anthropic/claude-fable-5",
        "x-ai/grok-4.20-beta",
    ),
    base_url="https://api.tokenrouter.com/v1",
)

register_provider(tokenrouter)
