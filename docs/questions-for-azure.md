# Questions for the Azure-connected agent

Hand this to an agent/tooling that has access to Azure AI Foundry and the
Azure AI Search service, to resolve the open unknowns from the flow audit
(see [flow-structure.md](flow-structure.md) §6). Redact any secrets/keys in
the answers.

**Context:** Azure ML Prompt Flow `template_chat_flow` queries Azure AI Search
on endpoint `https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net`. Two
indexes matter: `ndeee` (via a `promptflow_vectordb` index lookup) and
`wps-diain` (queried directly by the `wps_api` node).

## Q1 — The `ndeee` index (NDE / PMI lookup)

The flow's index config maps `content: line_class`, `metadata: pmi_percent`,
semantic configuration `ndeee-semantic-configuration`.

1. Dump the full index schema (field names + types).
2. Run a keyword search for one line class (e.g. `150A20`), `top=1`, and paste
   the **raw result document exactly as returned**.
3. Specifically: what does the retrieved document's **content / page_content**
   field contain — just the bare line class (e.g. `"150A20"`), or a full
   sentence like `"... Material Alloy 20. PMI 100.0."`? And what is the **type**
   of `pmi_percent` (integer `100`, string `"100"`, or float `100.0`)?

> Why: determines whether the `material` node (parses `"Material X"` out of the
> content) and `nde_py` (`pmi == 100`) can work, or are mis-wired.

## Q2 — The `wps-diain` index (WPS / PWHT lookup)

1. Dump the full index schema.
2. Confirm these fields exist and their types: `line_class`, `dia_in1`,
   `dia_in2`, `pwht`. What are `pwht`'s actual values (e.g. `Y`/`N`,
   `Yes`/`No`)?
3. Confirm a semantic configuration named `wps-diain-semantic-configuration`
   exists.
4. Paste one sample document.

> Why: confirms `wps_api` + `pwht_check` hit real fields and that `pwht` starts
> with `Y` as the code assumes.

## Q3 — Separate material index? + deployments exist?

1. List all Azure AI Search indexes on that endpoint. Is there any index
   dedicated to **material / CS-SS classification** (separate from `ndeee`)?
2. Under the Azure OpenAI connection `pf-openai-use2-id-auth`, confirm these
   deployments exist: `gpt-4o-mini-gs-2024-07-18`, `gpt-4o-gs-2024-05-13`,
   `text-embedding-ada-002-gs-2`.

> Why: tells us if `material` was meant to point at a different index, and
> whether the flow can run end-to-end.

## Optional extras (if there's time)

- Which `api-version` does the search service expect? (The flow uses
  `2023-11-01`.)
- Do the connections `pf-openai-use2-id-auth` and `pf-t332-t-cog` still resolve
  in the workspace?
- For `ndeee`, is the embedding field populated (vector search) or is it
  keyword-only? (The flow uses `query_type: Keyword`.)
