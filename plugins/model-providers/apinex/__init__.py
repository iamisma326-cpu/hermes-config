"""APINEX provider profile (OpenAI-compatible aggregator)."""

from providers import register_provider
from providers.base import ProviderProfile


apinex = ProviderProfile(
    name="apinex",
    aliases=("apinex-bond", "apx"),
    env_vars=("APINEX_API_KEY",),
    display_name="APINEX",
    description="APINEX — multi-model OpenAI-compatible router (Claude, GPT, Gemini, DeepSeek, GLM, Qwen)",
    signup_url="https://apinex.bond/",
    fallback_models=(
        "free/glm-5.3-flash",
        "free/qwen-3.8-max",
        "free/deepseek-v4-flash-0731",
        "free/gemini-3.8-flash",
        "free/gpt-5.6-luna",
        "gemini-3.1-pro",
        "claude-sonnet-5",
        "claude-opus-5",
        "gpt-5.6-sol",
        "gpt-6-astra",
        "deepseek-v4-pro",
        "glm-5.3",
        "kimi-k3",
        "grok-4.6",
    ),
    base_url="https://api.apinex.bond/v1",
)

register_provider(apinex)
