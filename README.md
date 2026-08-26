# TCO Job Pack Project

Prompt Flow → Microsoft Agent Framework (MAF) migration and job-pack generation POC.

The flow turns a free-text piping repair request into a structured job-pack
scope. It runs today as an Azure ML **Prompt Flow** DAG; the logic has been
factored into a runtime-agnostic Python package to make the MAF migration
straightforward.

## Layout

```
flow.dag.yaml         Prompt Flow graph (nodes, edges, LLM + package nodes)
flow.meta.yaml        Prompt Flow metadata
requirements.txt      Flow runtime dependencies

pf_jobpack/           Pure-Python core logic (NO promptflow import)
  extraction.py         free text/JSON -> 15-field scope state
  state.py              load / merge / validate / route conversation state
  search.py             Azure AI Search query building + HTTP client
  pwht.py               PWHT flag evaluation
  nde.py                NDE lookup evaluation
  material.py           material (CS/SS) classification
  template.py           job-pack scope text assembly

nodes/                Thin Prompt Flow @tool adapters (DAG entry points).
                      Each just calls the matching pf_jobpack function.

prompts/              Jinja2 templates for the LLM nodes
  spell_check.jinja2
  ask_or_finalize.jinja2
  final.jinja2

archive/              Untouched original export, kept for reference only.
  baseline-2026-08-24/  Original PF files + source data (Tracker, Procedures,
                        Samples, Isometrics, Templates).
```

## Design principle

- **`pf_jobpack/`** holds all business logic and imports nothing from
  Prompt Flow, so it can be unit-tested locally and reused by the future MAF
  agents unchanged.
- **`nodes/`** contains only glue: a `@tool`-decorated function per DAG node
  that forwards its inputs to `pf_jobpack`. This is the only layer that is
  Prompt Flow specific.

See [docs/flow-structure.md](docs/flow-structure.md) for the node-by-node map,
[docs/azure-environment.md](docs/azure-environment.md) for VDI / Azure facts,
and [docs/questions-for-azure.md](docs/questions-for-azure.md) for copy-paste
agent checklists.

## Running locally

Use an isolated environment (do not install into the base system):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pf flow test --flow . --inputs question="Replace leaking pipe 051-TL01-1/2-150H03 at TP-001"
```

The `nde` node is a `promptflow_vectordb` package tool and the `spell_check` /
`ask_or_finalize` / `final` nodes call Azure OpenAI, so a full run needs the
`pf-openai-use2-id-auth` connection and Azure AI Search access configured.

## Security note

`flow.dag.yaml` still contains a hardcoded Azure AI Search `api_key` on the
`wps_api` node (inherited from the original export). This key is also present in
git history under `archive/`. It should be **rotated** and moved to a Prompt
Flow connection / environment variable rather than committed in the DAG.

## Data

There is no separate `data/` directory. Source reference data lives under
`archive/baseline-2026-08-24/docs/jp/` — notably `Tracker (version 1)_ID003.xlsx`
and the `Procedures/` WPS/NDE tables used to build the Azure AI Search indexes.
