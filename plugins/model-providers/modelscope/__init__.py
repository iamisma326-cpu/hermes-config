"""ModelScope provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

modelscope = ProviderProfile(
    name="modelscope",
    aliases=("ms",),
    env_vars=("MODELSCOPE_API_KEY",),
    display_name="ModelScope",
    description="ModelScope Inference API (OpenAI-compatible)",
    signup_url="https://modelscope.cn/my/myaccesstoken",
    fallback_models=("Qwen/Qwen3.8-27B",),
    base_url="https://api-inference.modelscope.cn/v1",
)

register_provider(modelscope)
