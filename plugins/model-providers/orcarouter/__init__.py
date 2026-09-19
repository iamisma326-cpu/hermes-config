"""OrcaRouter provider profile."""

from providers import register_provider
from providers.base import ProviderProfile


orcarouter = ProviderProfile(
    name="orcarouter",
    aliases=("orca-router", "orca"),
    env_vars=("ORCAROUTER_API_KEY",),
    display_name="OrcaRouter",
    description="OrcaRouter — multi-model OpenAI-compatible router",
    signup_url="https://orcarouter.ai/",
    fallback_models=(
        "orcarouter/auto",
        "orcarouter/fusion",
        "orcarouter/fusion-flash",
        "orcarouter/free",
    ),
    base_url="https://api.orcarouter.ai/v1",
)

register_provider(orcarouter)
