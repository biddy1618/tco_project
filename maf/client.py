"""MAF chat client.

Default is Foundry / AIServices (``pf-t332-t-aif-use2-c3``). Set
``AZURE_OPENAI_ENDPOINT`` to force the classic Azure OpenAI resource
(``pf-t332-openai-use2``).
"""

from __future__ import annotations

import os
from typing import Any

from azure.identity.aio import AzureCliCredential
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatClient

# Defaults match docs/azure-environment.md (not secrets).
FOUNDRY_ENDPOINT = "https://pf-t332-t-aif-use2-c3.cognitiveservices.azure.com/"
CLASSIC_ENDPOINT = "https://pf-t332-openai-use2.openai.azure.com/"
DEFAULT_DEPLOYMENT = "gpt-4o-mini-gs-2024-07-18"
# PF ``ask_or_finalize`` / ``final`` node. Same name on Foundry and classic.
ASK_OR_FINALIZE_DEPLOYMENT = "gpt-4o-gs-2024-05-13"


def make_chat_client(
    *,
    endpoint: str | None = None,
    deployment: str | None = None,
) -> Any:
    """Return a chat client. ``model`` is the Azure *deployment name*.

    Foundry is the default. Classic OpenAI is used when ``endpoint`` is passed
    or ``AZURE_OPENAI_ENDPOINT`` is set (so an ``OPENAI_API_KEY`` cannot send
    traffic to public OpenAI on that path).
    """
    model = deployment or os.environ.get(
        "AZURE_OPENAI_CHAT_MODEL", DEFAULT_DEPLOYMENT
    )
    credential = AzureCliCredential()
    classic = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
    if classic:
        return OpenAIChatClient(
            model=model,
            azure_endpoint=classic,
            credential=credential,
        )
    return FoundryChatClient(
        project_endpoint=os.environ.get(
            "FOUNDRY_PROJECT_ENDPOINT", FOUNDRY_ENDPOINT
        ),
        model=model,
        credential=credential,
    )


def agent_text(result: object) -> str:
    """Normalize ``agent.run(...)`` output to a plain string."""
    if isinstance(result, str):
        return result.strip()
    text = getattr(result, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return str(result).strip()
