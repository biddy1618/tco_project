"""Slice 3: slice 2 + WPS/NDE/material lookups + template + final.

Maps Prompt Flow from ``wps_json_builder`` through ``final``. Incomplete
turns still ask a question (Search is a no-op passthrough). Complete turns
query Azure AI Search with ``AzureCliCredential`` (or ``AZURE_SEARCH_API_KEY``).

From the repo root, conda env ``maf``:

    python -m maf.slice3
    python -m maf.slice3 --history history.json "2 inch"
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Never

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

from maf.client import ASK_OR_FINALIZE_DEPLOYMENT, agent_text, make_chat_client
from maf.prompts import FINAL
from maf.search_client import WPS_INDEX, nde_lookup_items, run_search
from maf.trace import debug, setup, step
from maf.slice2 import (
    TC001,
    AskOrFinalizeExecutor,
    ExtractionExecutor,
    LoadStateExecutor,
    MergeStateExecutor,
    SpellCheckExecutor,
    ValidationExecutor,
    _append_history,
    _read_history,
)
from pf_jobpack.material import check_material_ss
from pf_jobpack.nde import check_nde_search
from pf_jobpack.pwht import check_pwht_flag
from pf_jobpack.search import build_wps_query
from pf_jobpack.state import route_prev
from pf_jobpack.template import build_job_pack


class RouteContinueExecutor(Executor):
    """Prompt Flow ``router`` — continue the graph instead of yielding."""

    @handler
    async def route(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        routed = route_prev(payload["answer"])
        step("router", kind=routed.get("kind"))
        await ctx.send_message({**payload, "route": routed})


class WpsBuilderExecutor(Executor):
    """Prompt Flow ``wps_json_builder``."""

    @handler
    async def build(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        routed = payload["route"]
        body = build_wps_query(
            as_string=routed.get("as_string") or "",
            as_dict=routed.get("as_dict") or {},
        )
        step(
            "wps_json_builder",
            passthrough=isinstance(body, str),
        )
        await ctx.send_message({**payload, "wps_body": body})


class WpsApiExecutor(Executor):
    """Prompt Flow ``wps_api`` (index ``wps-diain``)."""

    @handler
    async def search(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        result = run_search(WPS_INDEX, payload["wps_body"])
        hits = (
            len(result.get("value") or [])
            if isinstance(result, dict)
            else 0
        )
        step("wps_api", index=WPS_INDEX, hits=hits)
        await ctx.send_message({**payload, "wps_raw": result})


class PwhtExecutor(Executor):
    """Prompt Flow ``pwht_check``."""

    @handler
    async def check(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        line_class = (payload.get("state") or {}).get("line_class") or ""
        wps_result = check_pwht_flag(payload["wps_raw"], line_class)
        step("pwht_check", line_class=line_class, wps_result=wps_result)
        await ctx.send_message({**payload, "wps_result": wps_result})


class NdeExecutor(Executor):
    """Prompt Flow ``nde`` — skipped when ``complete`` is false."""

    @handler
    async def lookup(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        if not payload.get("complete"):
            step("nde", skipped=True)
            await ctx.send_message({**payload, "nde_hits": []})
            return
        line_class = (payload.get("state") or {}).get("line_class") or ""
        hits = nde_lookup_items(line_class)
        step("nde", line_class=line_class, hits=len(hits))
        await ctx.send_message({**payload, "nde_hits": hits})


class NdePyExecutor(Executor):
    """Prompt Flow ``nde_py``."""

    @handler
    async def evaluate(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        if not payload.get("complete"):
            step("nde_py", skipped=True)
            await ctx.send_message({**payload, "nde_result": None})
            return
        line_class = (payload.get("state") or {}).get("line_class") or ""
        nde_result = check_nde_search(payload.get("nde_hits") or [], line_class)
        step("nde_py", nde_result=nde_result)
        await ctx.send_message({**payload, "nde_result": nde_result})


class MaterialExecutor(Executor):
    """Prompt Flow ``material``."""

    @handler
    async def classify(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        material = check_material_ss(payload.get("nde_hits") or [])
        step("material", material=material)
        await ctx.send_message({**payload, "material": material})


class TemplateExecutor(Executor):
    """Prompt Flow ``template``."""

    @handler
    async def assemble(self, payload: dict, ctx: WorkflowContext[dict]) -> None:
        pack = build_job_pack(
            payload["answer"],
            payload.get("nde_result"),
            payload.get("wps_result"),
            payload.get("material"),
        )
        if isinstance(pack, dict):
            source = pack.get("final_text") or json.dumps(pack, default=str)
        else:
            source = pack
        step(
            "template",
            passthrough=not isinstance(pack, dict),
            chars=len(str(source)),
        )
        await ctx.send_message({**payload, "template": source})


class FinalExecutor(Executor):
    """Prompt Flow ``final`` (gpt-4o)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._agent = make_chat_client(
            deployment=ASK_OR_FINALIZE_DEPLOYMENT
        ).as_agent(
            name="final",
            instructions=FINAL,
        )

    @handler
    async def format_pack(
        self, payload: dict, ctx: WorkflowContext[Never, dict]
    ) -> None:
        step("final")
        result = await self._agent.run(str(payload.get("template") or ""))
        text = agent_text(result)
        debug("final", answer=text)
        await ctx.yield_output(
            {
                "answer": text,
                "complete": payload.get("complete"),
                "missing": payload.get("missing"),
                "merge_state": payload["merge_state"],
                "route": payload.get("route"),
                "wps_result": payload.get("wps_result"),
                "nde_result": payload.get("nde_result"),
                "material": payload.get("material"),
            }
        )


def build_workflow():
    load = LoadStateExecutor(id="load_state")
    spell = SpellCheckExecutor(id="spell_check")
    extract = ExtractionExecutor(id="extraction")
    merge = MergeStateExecutor(id="merge_state")
    validate = ValidationExecutor(id="validation")
    ask = AskOrFinalizeExecutor(id="ask_or_finalize")
    router = RouteContinueExecutor(id="router")
    wps_body = WpsBuilderExecutor(id="wps_json_builder")
    wps_api = WpsApiExecutor(id="wps_api")
    pwht = PwhtExecutor(id="pwht_check")
    nde = NdeExecutor(id="nde")
    nde_py = NdePyExecutor(id="nde_py")
    material = MaterialExecutor(id="material")
    template = TemplateExecutor(id="template")
    final = FinalExecutor(id="final")
    return (
        WorkflowBuilder(name="slice3_lookups_and_final", start_executor=load)
        .add_edge(load, spell)
        .add_edge(spell, extract)
        .add_edge(extract, merge)
        .add_edge(merge, validate)
        .add_edge(validate, ask)
        .add_edge(ask, router)
        .add_edge(router, wps_body)
        .add_edge(wps_body, wps_api)
        .add_edge(wps_api, pwht)
        .add_edge(pwht, nde)
        .add_edge(nde, nde_py)
        .add_edge(nde_py, material)
        .add_edge(material, template)
        .add_edge(template, final)
        .build()
    )


async def run(question: str, chat_history: list | None = None) -> dict:
    setup()
    history = chat_history or []
    step("slice3", history_turns=len(history))
    result = await build_workflow().run(
        {"question": question, "chat_history": history}
    )
    outputs = result.get_outputs()
    if not outputs:
        raise RuntimeError("Workflow produced no output (check yield_output).")
    return outputs[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MAF slice 3: Search lookups, template, and final job pack"
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=TC001,
        help="This turn's repair-scope text (default: TC-001)",
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
