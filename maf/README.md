# MAF migration (side-by-side with Prompt Flow)

Prompt Flow at the repo root is unchanged. This folder is the Microsoft Agent
Framework rewrite, built **one slice at a time**. Python logic stays in
`pf_jobpack/`; only LLM nodes and graph wiring are new.

| Slice | PF nodes | Status |
|---|---|---|
| 1 | `spell_check` → `extraction` | run on VDI |
| 2 | `load_state` → `merge_state` → `validation` → `ask_or_finalize` (+ `router`) | **run on VDI** |
| 3 | complete-gate → WPS/NDE/material → `template` → `final` | not started |

Client: `OpenAIChatClient` + `AzureCliCredential` against classic Azure OpenAI
(`https://pf-t332-openai-use2.openai.azure.com/`). No Foundry project. See
[docs/azure-environment.md](../docs/azure-environment.md).

## Run slice 1 (corporate VDI)

Python 3.10+ (conda env `maf`). From the **repo root** so `pf_jobpack` imports:

```powershell
conda activate maf
az account show   # must be T332 - TCO
cd path\to\tco_jp_project
python -m maf.slice1
```

Default input is Tracker TC-001. Pass other text as an argument:

```powershell
python -m maf.slice1 "051-TL01-1/2-150H03. Repleacement of damaged pipe section."
```

Optional env overrides (defaults are already the T332 resource):

```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://pf-t332-openai-use2.openai.azure.com/"
$env:AZURE_OPENAI_CHAT_MODEL = "gpt-4o-mini-gs-2024-07-18"
```

Expect JSON with `corrected` (spell-check output) and `state` (15-field dict).
On TC-001, `state.line_class` should be a legacy-mapped class (e.g. `150H25`
from `150H03`) and `state.placeholders_TP` should include `TP-001` / `TP-002`.

## Run slice 2 (corporate VDI)

Same env. First turn with empty history (default TC-001). Validation treats
`false` and `[]` as filled, so TC-001 is usually **complete** and
`ask_or_finalize` should return JSON (`route.kind` = `json`):

```powershell
python -m maf.slice2
```

Incomplete first turn (model should **ask** one question, `route.kind` = `string`):

```powershell
python -m maf.slice2 "replace the leaking valve"
```

Second turn, carrying `merge_state` like Prompt Flow `chat_history`:

```powershell
python -m maf.slice2 --history history.json "replace the leaking valve"
python -m maf.slice2 --history history.json "line class 150H03, 2 inch, insulated, no heat tracing"
```

`--history` is created if missing and appended after each successful run.
Output JSON: `answer` (what the user would see), `complete`, `missing`,
`merge_state` (feed the next turn), `route` (`json` vs `string`).
