# MAF migration (side-by-side with Prompt Flow)

Prompt Flow at the repo root is unchanged. This folder is the Microsoft Agent
Framework rewrite, built **one slice at a time**. Python logic stays in
`pf_jobpack/`; only LLM nodes and graph wiring are new.

| Slice | PF nodes | Status |
|---|---|---|
| 1 | `spell_check` → `extraction` | working |
| 2 | `load_state` → `merge_state` → `validation` → `ask_or_finalize` (+ `router`) | working |
| 3 | complete-gate → WPS/NDE/material → `template` → `final` | ready to run |

Client: `FoundryChatClient` + `AzureCliCredential` against
`https://pf-t332-t-aif-use2-c3.cognitiveservices.azure.com/` (same deployment
names as Prompt Flow). Classic Azure OpenAI is an opt-in fallback. See
[docs/azure-environment.md](../docs/azure-environment.md).

Python 3.10+. Install with `pip install -r maf/requirements.txt` unless
`agent_framework` is already on the interpreter. From the **repo root**:

```bash
az account show   # must be T332 - TCO
python -m maf.slice1
python -m maf.slice2
python -m maf.slice3
```

Optional env overrides:

```bash
# Default Foundry endpoint (unset = use the documented default)
export FOUNDRY_PROJECT_ENDPOINT="https://pf-t332-t-aif-use2-c3.cognitiveservices.azure.com/"

# Force classic Azure OpenAI instead of Foundry
export AZURE_OPENAI_ENDPOINT="https://pf-t332-openai-use2.openai.azure.com/"

export AZURE_OPENAI_CHAT_MODEL="gpt-4o-mini-gs-2024-07-18"
```

Windows PowerShell: `$env:FOUNDRY_PROJECT_ENDPOINT = "..."`.

Logs go to **stderr** (JSON still prints on stdout). Each node logs when it
runs (`load_state`, `spell_check`, `nde skipped=True`, …). More detail:

```bash
export MAF_LOG=DEBUG
```

PowerShell: `$env:MAF_LOG = "DEBUG"`.

## Slice 1

Default input is Tracker TC-001. Expect JSON with `corrected` and `state`
(15 fields). `state.line_class` is legacy-mapped (e.g. `150H03` → `150H25`);
`placeholders_TP` should include `TP-001` / `TP-002`. `dia_in` is often `[]`
because `1/2` in the line id is not parsed as NPS.

```bash
python -m maf.slice1 "051-TL01-1/2-150H03. Repleacement of damaged pipe section."
```

## Slice 2

Merge + validate + ask-or-finalize. Empty `[]` from extraction does **not**
overwrite `null` in merge, so TC-001 usually **asks for diameter**
(`missing: ["dia_in"]`, `route.kind` = `string`):

```bash
python -m maf.slice2
python -m maf.slice2 "replace the leaking valve"
```

Carry `merge_state` across turns (Prompt Flow `chat_history`):

```bash
python -m maf.slice2 --history history.json "replace the leaking valve"
python -m maf.slice2 --history history.json "line class 150H03, 2 inch, insulated, no heat tracing"
```

`--history` is created if missing and appended after each successful run.
Output: `answer`, `complete`, `missing`, `merge_state`, `route` (`json` vs
`string`).

## Slice 3

Slice 2 plus WPS (`wps-diain`), NDE/material (`ndeee`), `template`, and
`final`. Search uses `AzureCliCredential` (no key in the repo). Incomplete
turns still only ask; Search is not hit for a follow-up question string.

```bash
python -m maf.slice3
python -m maf.slice3 --history history.json "2 inch, NPS"
```

Output adds `wps_result`, `nde_result`, `material`. The chat `answer` is
either the follow-up question or the formatted job pack.

## Requirements

| File | For |
|---|---|
| `requirements.txt` (repo root) | Prompt Flow / Azure ML |
| `maf/requirements.txt` | MAF slices only (`agent-framework`, `azure-identity`) |

Do not `pip freeze` a full workstation env into either file.
