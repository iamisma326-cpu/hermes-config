"""Freemodel provider profile (OpenAI-compatible)."""

from providers import register_provider
from providers.base import ProviderProfile

freemodel = ProviderProfile(
    name="freemodel",
    aliases=("fmcc", "freemodelcc"),
    env_vars=("FREEMODEL_API_KEY",),
    display_name="Freemodel CC",
    description="Freemodel.cc — OpenAI-compatible provider (Claude models)",
    signup_url="https://cc.freemodel.dev/",
    fallback_models=(
        "claude-opus-5",
        "claude-sonnet-5",
        "claude-haiku-4-5-20251001",
        "claude-fable-5-1",
    ),
    base_url="https://cc.freemodel.dev/v1",
)

register_provider(freemodel)