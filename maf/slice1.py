"""Slice 1: spell_check (LLM) -> extraction (pf_jobpack).

Maps Prompt Flow nodes ``spell_check`` and ``extraction``. From the repo root:

    python -m maf.slice1
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Never

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

from maf.client import agent_text, make_chat_client
from maf.prompts import SPELL_CHECK
from maf.trace import setup, step
from pf_jobpack.extraction import build_scope_json_from_input

# Tracker TC-001 "deducted prompt" (same text used while learning the PF DAG).
TC001 = (
    "051-TL01-1/2-150H03. Dismantle clamp and replace damaged pipe section. "
    "Tie-ins at TP-001 and TP-002. Insulated, no heat tracing. "
    "Process conditions: Pdes [TBD], Poper [TBD], Tdes [TBD], Toper [TBD]."
)


class SpellCheckExecutor(Executor):
    """Prompt Flow ``spell_check`` LLM node."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._agent = make_chat_client().as_agent(
            name="spell_check",
            instructions=SPELL_CHECK,
        )

    @handler
    async def correct(self, question: str, ctx: WorkflowContext[str]) -> None:
        step("spell_check")
        result = await self._agent.run(question)
        await ctx.send_message(agent_text(result))


class ExtractionExecutor(Executor):
    """Prompt Flow ``extraction`` Python node — same ``pf_jobpack`` function."""

    @handler
    async def extract(
        self, corrected: str, ctx: WorkflowContext[Never, dict]
    ) -> None:
        state = build_scope_json_from_input(corrected)
        step(
            "extraction",
            line_class=state.get("line_class"),
            scope_type=state.get("scope_type"),
        )
        await ctx.yield_output({"corrected": corrected, "state": state})


def build_workflow():
    spell = SpellCheckExecutor(id="spell_check")
    extract = ExtractionExecutor(id="extraction")
    return (
        WorkflowBuilder(name="slice1_spellcheck_extract", start_executor=spell)
        .add_edge(spell, extract)
        .build()
    )


async def run(question: str) -> dict:
    setup()
    step("slice1")
    result = await build_workflow().run(question)
    outputs = result.get_outputs()
    if not outputs:
        raise RuntimeError("Workflow produced no output (check yield_output).")
    return outputs[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="MAF slice 1: spell_check + extraction")
    parser.add_argument(
        "question",
        nargs="?",
        default=TC001,
        help="Repair-scope text (default: TC-001 deducted prompt)",
    )
    args = parser.parse_args()
    payload = asyncio.run(run(args.question))
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
