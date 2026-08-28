"""Slice 2: spell_check → extraction → load/merge/validate → ask_or_finalize.

Maps Prompt Flow through ``ask_or_finalize`` (and ``router``, so the output
says whether the model asked a question or returned JSON state).

From the repo root, conda env ``maf``:

    python -m maf.slice2
    python -m maf.slice2 "replace the leaking valve"
    python -m maf.slice2 --history history.json "I&E Job Pack 24-0101"
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Never

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

from maf.cases import resolve_question
from maf.client import ASK_OR_FINALIZE_DEPLOYMENT, agent_text, make_chat_client
from maf.prompts import ASK_OR_FINALIZE, SPELL_CHECK
from maf.trace import debug, setup, step
from pf_jobpack.extraction import build_scope_json_from_input
from pf_jobpack.state import load_state, merge_state, route_prev, validate_state


def _ask_user_message(state: dict, complete: bool, missing: list) -> str:
    return (
        "Current information:\n"
        f"{json.dumps(state, indent=2, default=str)}\n\n"
        f"Complete:\n{complete}\n\n"
        "Missing fields:\n"
        f"{json.dumps(missing, default=str)}"
    )


class LoadStateExecutor(Executor):
    """Prompt Flow ``load_state`` — prev merged state from chat_history."""

    @handler
    async def load(self, turn: dict, ctx: WorkflowContext[dict]) -> None:
        history = turn.get("chat_history") or []
        prev = load_state(history)
        step("load_state", history_turns=len(history))
        await ctx.send_message(
            {
                "question": turn.get("question") or "",
                "prev_state": prev,
            }
        )


class SpellCheckExecutor(Executor):
    """Prompt Flow ``spell_check`` (gpt-4o-mini)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._agent = make_chat_client().as_agent(
            name="spell_check",
            instructions=SPELL_CHECK,
        )

    @handler
    async def correct(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        step("spell_check")
        result = await self._agent.run(payload["question"])
        await ctx.send_message({**payload, "corrected": agent_text(result)})


class ExtractionExecutor(Executor):
    """Prompt Flow ``extraction``."""

    @handler
    async def extract(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        new_extraction = build_scope_json_from_input(payload["corrected"])
        step(
            "extraction",
            line_class=new_extraction.get("line_class"),
            scope_type=new_extraction.get("scope_type"),
        )
        await ctx.send_message({**payload, "new_extraction": new_extraction})


class MergeStateExecutor(Executor):
    """Prompt Flow ``merge_state``."""

    @handler
    async def merge(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        merged = merge_state(payload["prev_state"], payload["new_extraction"])
        step("merge_state")
        await ctx.send_message({**payload, "merge_state": merged})


class ValidationExecutor(Executor):
    """Prompt Flow ``validation``."""

    @handler
    async def validate(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        checked = validate_state(payload["merge_state"])
        step(
            "validation",
            complete=checked["complete"],
            missing=checked["missing"],
        )
        await ctx.send_message({**payload, **checked})


class AskOrFinalizeExecutor(Executor):
    """Prompt Flow ``ask_or_finalize`` (gpt-4o)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._agent = make_chat_client(
            deployment=ASK_OR_FINALIZE_DEPLOYMENT
        ).as_agent(
            name="ask_or_finalize",
            instructions=ASK_OR_FINALIZE,
        )

    @handler
    async def decide(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        user = _ask_user_message(
            payload["state"], payload["complete"], payload["missing"]
        )
        step("ask_or_finalize", complete=payload["complete"])
        result = await self._agent.run(user)
        text = agent_text(result)
        debug("ask_or_finalize", answer=text)
        await ctx.send_message({**payload, "answer": text})


class RouterExecutor(Executor):
    """Prompt Flow ``router`` — JSON state vs follow-up question."""

    @handler
    async def route(
        self, payload: dict, ctx: WorkflowContext[Never, dict]
    ) -> None:
        routed = route_prev(payload["answer"])
        step("router", kind=routed.get("kind"))
        await ctx.yield_output(
            {
                "answer": payload["answer"],
                "complete": payload["complete"],
                "missing": payload["missing"],
                "merge_state": payload["merge_state"],
                "route": routed,
            }
        )


def build_workflow():
    load = LoadStateExecutor(id="load_state")
    spell = SpellCheckExecutor(id="spell_check")
    extract = ExtractionExecutor(id="extraction")
    merge = MergeStateExecutor(id="merge_state")
    validate = ValidationExecutor(id="validation")
    ask = AskOrFinalizeExecutor(id="ask_or_finalize")
    router = RouterExecutor(id="router")
    return (
        WorkflowBuilder(name="slice2_state_and_ask", start_executor=load)
        .add_edge(load, spell)
        .add_edge(spell, extract)
        .add_edge(extract, merge)
        .add_edge(merge, validate)
        .add_edge(validate, ask)
        .add_edge(ask, router)
        .build()
    )


def _read_history(path: Path | None) -> list:
    if path is None or not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON list of chat turns")
    return data


def _append_history(path: Path, question: str, merge_state_out: dict) -> None:
    history = _read_history(path)
    history.append(
        {
            "inputs": {"question": question},
            "outputs": {"merge_state": merge_state_out},
        }
    )
    path.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")


async def run(question: str, chat_history: list | None = None) -> dict:
    setup()
    question = resolve_question(question)
    history = chat_history or []
    step("slice2", history_turns=len(history))
    result = await build_workflow().run(
        {"question": question, "chat_history": history}
    )
    outputs = result.get_outputs()
    if not outputs:
        raise RuntimeError("Workflow produced no output (check yield_output).")
    return outputs[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MAF slice 2: merge/validate state and ask or finalize"
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="TC-001",
        help="This turn's repair-scope text, or a Tracker ID like TC-001",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=None,
        help="JSON file of prior turns (PF-style outputs.merge_state). "
        "Updated in place after a successful run.",
    )
    args = parser.parse_args()
    history = _read_history(args.history)
    payload = asyncio.run(run(args.question, history))
    if args.history is not None:
        _append_history(args.history, args.question, payload["merge_state"])
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
