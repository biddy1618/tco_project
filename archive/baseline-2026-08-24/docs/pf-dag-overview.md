# Prompt Flow DAG Overview

Prompt Flow represents a workflow as a directed acyclic graph.

## Core idea

The flow starts with declared inputs, passes values from node to node, and ends with declared outputs. Each node only depends on earlier values, so the graph has no cycles.

## Node types used here

- `llm` nodes call an Azure OpenAI deployment with a prompt template.
- `python` nodes run local logic for extraction, validation, routing, and assembly.
- `package` nodes call a packaged tool such as vector search.

## How data moves

A node can reference prior values with `${node_name.output}` or `${inputs.input_name}`. That means the flow is mostly declarative: the DAG says what depends on what, and Prompt Flow schedules the execution.

## What this project does

This job-pack flow follows a pipeline:

1. Spell-check the user question.
2. Extract structured fields from the text.
3. Load prior conversation state.
4. Merge new and existing state.
5. Validate whether enough fields are present.
6. Ask for missing data or continue.
7. Look up WPS/PWHT and NDE data.
8. Assemble the final job-pack output.

## Why the root files stay for now

`flow.dag.yaml` still points to root-level prompt templates and Python modules. Until those references are updated together, the existing files should remain where they are so the current flow continues to work.
