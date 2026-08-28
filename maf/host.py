"""Foundry-facing host for slice 2 (chat UI / hosted agent).

``python -m maf.slice2`` stays the CLI. This module wraps the same graph so a
chat client can talk to it:

    python -m maf.host --once
    python -m maf.host --serve    # http://localhost:8088/responses

Foundry hosted agents speak the Responses protocol (``POST /responses`` with
``{"input": "..."}``). That is a conversation, not ``{question, chat_history}``,
so this agent reconstructs Prompt Flow ``chat_history`` from prior turns.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections.abc import AsyncIterable
from typing import Any
from uuid import uuid4

from agent_framework import (
    AgentResponse,
    AgentResponseUpdate,
    BaseAgent,
    Message,
)

from maf.client import agent_text
from maf.cases import resolve_question
from maf.slice2 import run as slice2_run

_STATE_FENCE = re.compile(r"```jp_state\s*(\{.*?\})\s*```", re.DOTALL)


def _is_user(msg: Any) -> bool:
    role = getattr(msg, "role", None)
    return "user" in str(role).lower()


def _message_text(msg: Any) -> str:
    if isinstance(msg, str):
        return msg.strip()
    text = getattr(msg, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    parts: list[str] = []
    for item in getattr(msg, "contents", None) or []:
        if isinstance(item, str) and item.strip():
            parts.append(item.strip())
            continue
        piece = getattr(item, "text", None)
        if isinstance(piece, str) and piece.strip():
            parts.append(piece.strip())
    return "\n".join(parts).strip()


def _as_messages(messages: Any) -> list[Any]:
    if messages is None:
        return []
    if isinstance(messages, (str, Message)):
        return [messages]
    return list(messages)


def _parse_merge_state(text: str) -> dict | None:
    match = _STATE_FENCE.search(text or "")
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    merged = payload.get("merge_state")
    return merged if isinstance(merged, dict) else None


def turn_from_messages(messages: Any) -> tuple[str, list[dict]]:
    """Last user text + Prompt Flow ``chat_history`` from earlier ``jp_state`` blocks."""
    history: list[dict] = []
    pending_question = ""
    question = ""
    for msg in _as_messages(messages):
        text = _message_text(msg)
        if not text:
            continue
        if _is_user(msg) or isinstance(msg, str):
            pending_question = text
            question = text
            continue
        merged = _parse_merge_state(text)
        if merged is None:
            continue
        history.append(
            {
                "inputs": {"question": pending_question},
                "outputs": {"merge_state": merged},
            }
        )
        pending_question = ""
    return question, history


def format_reply(payload: dict) -> str:
    blob = {
        "complete": payload.get("complete"),
        "missing": payload.get("missing"),
        "route": payload.get("route"),
        "merge_state": payload.get("merge_state"),
    }
    answer = str(payload.get("answer") or "").strip()
    return (
        f"{answer}\n\n```jp_state\n"
        f"{json.dumps(blob, indent=2, default=str)}\n```"
    )


class Slice2Agent(BaseAgent):
    """Slice 2 as a chat agent (not ``Workflow.as_agent()``).

    A custom agent is used because Foundry's Responses host passes the full
    transcript into ``Agent.run``. ``Workflow.as_agent()`` instead resumes
    checkpoints and often only forwards the latest user line, which would
    drop Prompt Flow ``merge_state``.
    """

    def __init__(self) -> None:
        super().__init__(
            name="tco-jobpack-slice2",
            description=(
                "Job-pack slice 2: spell-check, extract, merge, validate, "
                "then ask or finalize."
            ),
        )

    async def run(
        self,
        messages: Any = None,
        *,
        stream: bool = False,
        session: Any = None,
        **kwargs: Any,
    ) -> AgentResponse | AsyncIterable[AgentResponseUpdate]:
        del session, kwargs
        question, history = turn_from_messages(messages)
        if not question:
            raise ValueError("No user message in this turn.")
        payload = await slice2_run(question, history)
        reply = format_reply(payload)
        response = AgentResponse(
            messages=[Message("assistant", [reply])],
            response_id=str(uuid4()),
        )
        if not stream:
            return response

        async def _stream() -> AsyncIterable[AgentResponseUpdate]:
            yield AgentResponseUpdate(
                contents=list(response.messages[0].contents),
                role="assistant",
                response_id=response.response_id,
            )

        return _stream()


def _responses_server(agent: Slice2Agent):
    try:
        from agent_framework_foundry_hosting import ResponsesHostServer
    except ImportError:
        try:
            from agent_framework.foundry import ResponsesHostServer
        except ImportError as exc:
            raise ImportError(
                "ResponsesHostServer is not installed. In an isolated env: "
                "pip install agent-framework-foundry-hosting in an isolated env"
            ) from exc
    return ResponsesHostServer(agent)


async def _once(question: str) -> None:
    result = await Slice2Agent().run(question)
    print(agent_text(result))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Host MAF slice 2 as a Foundry Responses agent"
    )
    parser.add_argument(
        "--once",
        nargs="?",
        const="",
        metavar="QUESTION",
        help="Run one chat turn locally (default question: TC-001). No HTTP server.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Serve POST /responses on port 8088 (Foundry hosted-agent protocol).",
    )
    args = parser.parse_args()
    if args.once is not None:
        asyncio.run(_once(resolve_question(args.once or "TC-001")))
        return
    if not args.serve:
        parser.print_help()
        print("\nNeed --once or --serve.")
        raise SystemExit(2)
    _responses_server(Slice2Agent()).run()


if __name__ == "__main__":
    main()
