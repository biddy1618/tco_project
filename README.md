# TCO Job Pack Project

Prompt Flow → Microsoft Agent Framework (MAF) migration and job-pack generation POC.

The flow turns a free-text piping repair request into a structured job-pack
scope. It runs today as an Azure ML **Prompt Flow** DAG; the logic lives in a
runtime-agnostic Python package (`pf_jobpack`) so MAF can reuse it.

## Layout

```
flow.dag.yaml         Prompt Flow graph
flow.meta.yaml        Prompt Flow metadata
requirements.txt      Prompt Flow runtime dependencies

pf_jobpack/           Pure-Python core (no promptflow import)
nodes/                Thin Prompt Flow @tool adapters
prompts/              Jinja2 templates for LLM nodes
tests/                Offline unit tests (pytest)
maf/                  MAF rewrite, one slice at a time (does not replace PF yet)
archive/              Original PF export + Tracker / procedures (reference)
docs/                 Flow map and Azure inventory
```

## Design principle

- **`pf_jobpack/`** holds business logic and does not import Prompt Flow.
- **`nodes/`** is Prompt Flow glue only.
- **`maf/`** wraps the same `pf_jobpack` functions in Agent Framework executors.

See [docs/flow-structure.md](docs/flow-structure.md) for the DAG,
[docs/azure-environment.md](docs/azure-environment.md) for Azure resources, and
[maf/README.md](maf/README.md) to run MAF slices.

## Prompt Flow

Isolated env (do not install into the base interpreter):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pf flow test --flow . --inputs question="Replace leaking pipe 051-TL01-1/2-150H03 at TP-001"
```

Needs workspace connections `pf-openai-use2-id-auth` and Azure AI Search.

## MAF slices

Python 3.10+, `az login` on subscription **T332 - TCO**. If `agent_framework`
is not already installed:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r maf/requirements.txt
```

Use the corporate Artifactory PyPI index, not public PyPI. From the **repo
root**:

```bash
python -m maf.slice1
python -m maf.slice2
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Security

`flow.dag.yaml` still contains a hardcoded Azure AI Search `api_key` on
`wps_api` (also in `archive/`). Rotate it; do not send that value in a zip.

## Data

Tracker and procedure tables: `archive/baseline-2026-08-24/docs/jp/`.

## Sharing a zip

**Include**

- `README.md`, `flow.dag.yaml` (key redacted), `flow.meta.yaml`
- `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `conftest.py`
- `pf_jobpack/`, `nodes/`, `prompts/`, `tests/`, `maf/`
- `docs/flow-structure.md`, `docs/azure-environment.md`
- `archive/` only if they need Tracker / procedure source (large)

**Omit**

- `docs/questions-for-azure.md` (internal checklist)
- `__pycache__/`, `.venv/`, `.promptflow/`, `.runs/`, `history.json`, `.env`
- `.git/` unless they asked for history
