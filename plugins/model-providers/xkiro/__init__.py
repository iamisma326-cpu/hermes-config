"""XKiro provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

xkiro = ProviderProfile(
    name="xkiro",
    aliases=("xt",),
    env_vars=("XKIRO_API_KEY",),
    display_name="XKiro",
    description="XKiro — OpenAI-compatible aggregator (112 models: GPT, Claude, Gemini, GLM, Qwen, DeepSeek, Kimi, Mistral; ~35 free-tier)",
    signup_url="https://xkiro.com/",
    fallback_models=(
        "qwen/qwen3.8-max:free",
        "mistralai/mistral-large-2512",
        "qwen/qwen3.7-max:free",
        "qwen/qwen3-coder-plus:free",
        "mistralai/mistral-medium-3.5",
        "qwen/qwen3-max:free",
        "deepseek/deepseek-v4.1-flash",
        "z-ai/glm-5.3",
        "anthropic/claude-sonnet-5",
    ),
    base_url="https://api.xkiro.com/v1",
)

register_provider(xkiro)