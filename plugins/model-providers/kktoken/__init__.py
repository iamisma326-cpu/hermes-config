"""KKToken provider profile (OpenAI-compatible, new-api distributor)."""

from providers import register_provider
from providers.base import ProviderProfile

kktoken = ProviderProfile(
    name="kktoken",
    aliases=("kkt",),
    env_vars=("KKTOKEN_API_KEY",),
    display_name="KKToken",
    description="KKToken.cc — OpenAI-compatible new-api distributor (Claude, GPT, Gemini, DeepSeek, Grok). /models returns empty and chat returns 503 model_not_found; possibly defunct — verify before relying on it.",
    signup_url="https://kktoken.cc/",
    fallback_models=(),
    base_url="https://kktoken.cc/v1",
)

register_provider(kktoken)