"""ExperientialLabs provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

experientiallabs = ProviderProfile(
    name="experientiallabs",
    aliases=("xpl", "experiential"),
    env_vars=("EXPERIENTIALLABS_API_KEY",),
    display_name="ExperientialLabs",
    description="ExperientialLabs — OpenAI-compatible aggregator (318 models: Claude, GPT, Gemini, GLM, DeepSeek, Qwen, Grok, Kimi)",
    signup_url="https://experientiallabs.ai/",
    fallback_models=(
        "glm-5.3",
        "glm-5.3-flash",
        "claude-sonnet-5",
        "claude-opus-5",
        "gpt-5.6-luna",
        "gemini-3.8-flash",
        "deepseek-v4-flash",
        "qwen3.8-max",
        "kimi-k3",
    ),
    base_url="https://api.experientiallabs.ai/v1",
)

register_provider(experientiallabs)