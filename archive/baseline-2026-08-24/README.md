# PF Job Pack Project

Local working copy for the Prompt Flow to MAF migration and job-pack generation POC.

## Proposed layout

- `src/pf_jobpack/` - Python package code for the implementation.
- `prompts/` - Jinja and prompt templates.
- `configs/` - Flow and runtime configuration.
- `data/raw/` - Source inputs and reference artifacts.
- `data/processed/` - Derived data and cleaned outputs.
- `docs/` - Project notes, specs, and migration references.
- `scripts/` - Utility scripts and one-off helpers.
- `tests/unit/` - Unit tests.
- `tests/integration/` - Integration and parity tests.
- `artifacts/` - Generated outputs and local run results.

## Current state

The current Prompt Flow still runs from the repo root because `flow.dag.yaml` points to root-level templates and Python modules. I have already moved the two safe reference artifacts into the new layout:

- `docs/Narrative markup rev2 2.docx`
- `data/raw/Tracker (version 1)_ID003 1.xlsx`

The flow implementation files stay at the root for now so the graph keeps working. We can move them later in a controlled pass after we update the DAG paths.

## How Prompt Flow DAGs work

Prompt Flow treats the flow as a directed acyclic graph, not a linear script.

- `inputs` define the entry points exposed to the user or upstream caller.
- Each `node` has a type such as `llm`, `python`, or `package`.
- A node receives values through `${...}` references to earlier node outputs or flow inputs.
- The graph must stay acyclic, so data only moves forward.
- `outputs` map one or more internal node results to the public flow result.
- `activate` blocks let a node run only when a condition is met.
- `source.path` points to the prompt template or Python file that implements the node.

In this project, the flow is a staged pipeline: spell-correct the user input, extract structured fields, merge them with history, validate completeness, ask for missing details or finalize, then look up WPS/NDE data and assemble the final job pack text.

## Next move

Once we are ready to refactor safely, the order should be: move prompts and docs, then relocate Python code into `src/pf_jobpack/`, then update `flow.dag.yaml` to point at the new paths.
