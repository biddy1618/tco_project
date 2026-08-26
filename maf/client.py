"""Classic Azure OpenAI client for MAF (no Foundry project on this subscription)."""

from __future__ import annotations

import os

from azure.identity.aio import AzureCliCredential
from agent_framework.openai import OpenAIChatClient

# Defaults match docs/azure-environment.md (not secrets).
DEFAULT_ENDPOINT = "https://pf-t332-openai-use2.openai.azure.com/"
DEFAULT_DEPLOYMENT = "gpt-4o-mini-gs-2024-07-18"
# PF ``ask_or_finalize`` / ``final`` node.
ASK_OR_FINALIZE_DEPLOYMENT = "gpt-4o-gs-2024-05-13"


def make_chat_client(
    *,
    endpoint: str | None = None,
    deployment: str | None = None,
) -> OpenAIChatClient:
    """OpenAIChatClient forced onto the classic Azure OpenAI resource.

    ``model`` is the *deployment name* on that resource. ``credential`` plus
    ``azure_endpoint`` keep the call on Azure even if ``OPENAI_API_KEY`` is set.
    """
    return OpenAIChatClient(
        model=deployment or os.environ.get("AZURE_OPENAI_CHAT_MODEL", DEFAULT_DEPLOYMENT),
        azure_endpoint=endpoint
        or os.environ.get("AZURE_OPENAI_ENDPOINT", DEFAULT_ENDPOINT),
        credential=AzureCliCredential(),
    )


def agent_text(result: object) -> str:
    """Normalize ``agent.run(...)`` output to a plain string."""
    if isinstance(result, str):
        return result.strip()
    text = getattr(result, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return str(result).strip()
