# Questions for the Azure-connected agent

This file has **two independent checklists**. Hand the one you need:

1. **Q1–Q3** (already answered 2026-08-25) — Azure AI Search index schemas
   and OpenAI deployments. See [flow-structure.md](flow-structure.md) §6.
2. **Q4** (below, after the Q1–Q3 answers) — Microsoft Agent Framework (MAF)
   readiness on the **corporate VDI**. Copy that whole section to the VDI
   agent. It is written as a strict step-by-step script for a small model.

Redact any secrets/keys in the answers.

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

---

# Answers (from live Azure, 2026-08-25)

Queried against the live service via the Azure AI Search REST API
(`api-version=2023-11-01`) using an AAD token, and via `az cognitiveservices`
for the OpenAI deployments. Subscription: **T332 - TCO**.

## A1 — The `ndeee` index

**1. Full schema (field : type — retrievable/searchable/filterable):**

| Field | Type | Retrievable | Searchable | Filterable |
|---|---|---|---|---|
| `title` | Edm.String | ✅ | ❌ | ❌ |
| `id` | Edm.String | ✅ | ✅ | ✅ |
| `number` | Edm.String | ✅ | ❌ | ❌ |
| `line_class` | Edm.String | ✅ | ✅ | ✅ |
| `design_code` | Edm.String | ❌ | ❌ | ❌ |
| `design_temp_range_deg_c` | Edm.String | ❌ | ❌ | ❌ |
| `material` | Edm.String | ❌ | ❌ | ❌ |
| `rt_ut_nde_percent` | Edm.String | ❌ | ❌ | ❌ |
| `mt_pt_nde_percent` | Edm.String | ❌ | ❌ | ❌ |
| `nde_percent` | Edm.String | ❌ | ❌ | ❌ |
| `pmi_percent` | Edm.String | ✅ | ❌ | ❌ |
| `line_class_normalized` | Edm.String | ❌ | ❌ | ❌ |
| `content` | Edm.String | ✅ | ❌ | ❌ |
| `AzureSearch_DocumentKey` | Edm.String | ❌ | ❌ | ❌ |
| `metadata_storage_*` | (String/Int64/DateTimeOffset) | ❌ | ❌ | ❌ |

Semantic configuration `ndeee-semantic-configuration` **exists**.

**2. Raw result — search `150A20`, `top=1` (exactly as returned):**

```json
{
  "@search.score": 2.6473582,
  "title": "nde.csv",
  "id": "aHR0cHM6Ly9yYWdqcGJsb2IuYmxvYi5jb3JlLndpbmRvd3MubmV0L25kZS9uZGUuY3N2",
  "number": "1",
  "line_class": "150A20",
  "pmi_percent": "100",
  "content": "Pipe line class 150A20. Design code ASME B31.3. Design temperature range -40 / 200 deg C. Material Alloy 20. PMI 100.0."
}
```

**3. The critical answers:**
- `content` is a **full sentence**, not a bare line class:
  `"Pipe line class 150A20. Design code ASME B31.3. Design temperature range
  -40 / 200 deg C. Material Alloy 20. PMI 100.0."`
- `pmi_percent` type is **`Edm.String`**, value `"100"` (string — **not** int
  `100` or float `100.0`).

> **Implication:** The `material` node parsing `"Material X"` out of `content`
> is **correct and necessary** — the dedicated `material` field exists in the
> schema but is **`retrievable=false`**, so it is *not* returned by a query.
> Same for `nde_percent` (not retrievable). For `nde_py`, comparing
> `pmi == 100` must account for the value being the **string** `"100"` (and the
> content spells it as `PMI 100.0`), so a naive `int`/`== 100` check needs a
> cast or string compare.

## A2 — The `wps-diain` index

**1. Full schema:**

| Field | Type |
|---|---|
| `title` | Edm.String |
| `id` | Edm.String |
| `idid` | Edm.String |
| `line_class` | Edm.String |
| `design_code` | Edm.String |
| `temp_range_deg_c` | Edm.String |
| `material` | Edm.String |
| `dia_in` | Edm.String |
| `thickness_range_mm` | Edm.String |
| `wps_number` | Edm.String |
| `pwht` | Edm.String |
| `comments` | Edm.String |
| `line_class_normalized` | Edm.String |
| `content` | Edm.String |
| `dia_in1` | **Edm.Double** |
| `dia_in2` | **Edm.Double** |
| `AzureSearch_DocumentKey` | Edm.String |
| `metadata_storage_*` | (String/Int64/DateTimeOffset) |

**2. Confirmed fields & types:** `line_class` (String), `dia_in1`
(**Double**), `dia_in2` (**Double**), `pwht` (String) — all exist.
`pwht` distinct values across all 266 docs:

| pwht value | count |
|---|---|
| `N` | 128 |
| `Y` | 103 |
| *(empty)* | 18 |
| `N see Note (7)` | 17 |

So values are **`Y` / `N`** (not `Yes`/`No`), but note **18 blanks** and **17
rows literally `"N see Note (7)"`**.

**3.** Semantic configuration `wps-diain-semantic-configuration` **exists**.

**4. Sample documents (`search=*`, `top=2`):**

```json
[
  { "line_class": "150A20", "pwht": "N", "dia_in1": 0.5, "dia_in2": 4.0,
    "title": "wps-inch-output.csv", "idid": "0" },
  { "line_class": "150H5E", "pwht": "N", "dia_in1": 0.5, "dia_in2": 3.0,
    "title": "wps-inch-output.csv", "idid": "20" }
]
```

> **Implication:** `wps_api` + `pwht_check` hit real fields. The code's
> assumption that "PWHT required" == `pwht` starts with `Y` mostly holds, but
> the **`"N see Note (7)"`** rows start with `N` (safe) and the **blank** rows
> would evaluate as *not required* — confirm that's the intended default.

## A3 — Separate material index? + deployments

**1. All indexes on the endpoint** (33 total):
`asarindex`, `asarindex_2026`, `contoso-coffee-maker-manual`,
`contosoproductsindex`, `customs-declaration-others-index`,
`datamax-support-index`, `dd`, `dsh-index`, `hotel`, `idxr-downtime-ref`,
`idxr-iir-incident`, `idxr-oeimpact-incident`, `idxr-planned-worklist-ref`,
`idxr-technical-lessons-learned`, `json-indeces`, **`ndeee`**,
`nuriz1-asar-test-v2`, `nuriz1-asar-test`, `rag-jp-md`, `rag-jp-samples`,
`rag-jp-test`, `realdups`, `sql-index`, `stoic-fennel-dq0c6dd894`, `tcocont`,
`tcohrindex`, `tesindex`, `test-index-for-showcase`, `tesvectorindex`,
**`wps-diain`**, `znom-temp`, `znom-turnaroundtest`.

There is **no index dedicated to material / CS-SS classification**. Material
data lives **inside `ndeee`** (the `material` field / the `content` sentence).
So the `material` node was **not** meant to point at a different index — it
correctly reads from `ndeee`.

**2. Deployments under `pf-openai-use2-id-auth`** (resource
`pf-t332-openai-use2` / RG `pf-T332-t-cog`) — **all three confirmed present**:
- ✅ `gpt-4o-mini-gs-2024-07-18` (gpt-4o-mini, 2024-07-18)
- ✅ `gpt-4o-gs-2024-05-13` (gpt-4o, 2024-05-13)
- ✅ `text-embedding-ada-002-gs-2` (text-embedding-ada-002, 2)

## Optional extras

- **api-version:** `2023-11-01` works against the service (used for every
  query above). ✅
- **Connections:** the OpenAI resource behind `pf-openai-use2-id-auth`
  (`pf-t332-openai-use2`) resolves; the `pf-T332-t-cog` resource group /
  Cognitive resources resolve in the subscription. ✅
- **`ndeee` vector/keyword:** effectively **keyword-only** in practice — the
  only searchable fields are `line_class` and `id`; `content` and `pmi_percent`
  are `searchable=false`. Keyword search must target `line_class`, which is
  exactly what the flow does (`query_type: Keyword`). ✅

---

# Q4 — MAF readiness on the corporate VDI

**Copy everything from this heading down to the end of the "Report template"
section. Paste it as the entire prompt to the VDI agent. Do not summarise it.**

The VDI agent is a smaller model. It must follow the steps in order, run the
exact commands, and fill the report template. It must not invent endpoints,
must not install packages unless a step says so, and must not skip a failed
step.

---

## Prompt for the VDI agent (copy from here)

You are a local helper on a Windows corporate VDI. Your job is to check
whether Microsoft Agent Framework (MAF) can call Azure OpenAI from this
machine. You are **not** migrating code. You are **not** rewriting the Prompt
Flow. You only run checks and report facts.

### Hard rules

1. Work in PowerShell.
2. Activate the existing conda env named `maf` before any Python command:
   `conda activate maf`
3. Do **not** install packages unless a step below explicitly says to.
4. Do **not** install `azure-ai-evaluation`. That is for a later phase.
5. Do **not** install extra `agent-framework-*` packages. They are already
   present.
6. Do **not** use `pip install` against public pypi.org if Artifactory is
   configured. Use the already-configured index.
7. Do **not** print API keys, tokens, or connection strings. If a command
   would dump a secret, redact it as `***`.
8. If a command fails, stop that step, paste the **full error text**, then
   continue with the next step that does not depend on it.
9. When you finish, fill the **Report template** at the bottom. Use PASS /
   FAIL / SKIP / UNKNOWN only.

### Already known (do not re-ask the human)

These were already verified. Re-run the commands anyway and confirm they
still match. If they differ, report the new values.

| Fact | Expected value |
|---|---|
| Conda env | `maf` |
| Python | 3.11.15 |
| pip index | `artifactory.chevron.com/artifactory/api/pypi` (`pypi-local/simple`, `pypi-local-dev/simple`, `pypi/simple`) |
| `agent-framework` | 1.14.0 |
| `agent-framework-core` | 1.14.0 |
| `agent-framework-foundry` | 1.11.0 |
| `agent-framework-openai` | 1.13.0 |
| `agent-framework-azure-ai-search` | 1.0.0b260813 |
| Azure CLI subscription name | `T332 - TCO` |
| Azure CLI subscription id | `baa67dbf-45d0-4d84-b662-527186361068` |
| Azure CLI user | `Dauren.Baitursyn@tengizchevroil.com` |
| OpenAI resource group | `pf-T332-t-cog` |
| OpenAI resource name | `pf-t332-openai-use2` |
| Classic OpenAI endpoint | `https://pf-t332-openai-use2.openai.azure.com/` |
| Search endpoint | `https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net` |
| Smoke-test chat deployment | `gpt-4o-mini-gs-2024-07-18` |
| Production chat deployment (do not call yet) | `gpt-4o-gs-2024-05-13` |
| Embedding deployment (do not call yet) | `text-embedding-ada-002-gs-2` |

There is **no** `maf new` or `az maf create` command. A MAF project is a
Python package that imports `agent_framework`. Readiness = Python 3.10+ +
packages import + Azure auth + a successful chat completion.

### Step 0 — working directory

```powershell
pwd
conda activate maf
python --version
where python
```

Expected: Python 3.11.x, and the interpreter path should be inside the `maf`
conda env.

### Step 1 — confirm MAF packages import

```powershell
python -c "import agent_framework; print('agent_framework', getattr(agent_framework, '__version__', 'NO_VERSION'))"
python -c "from agent_framework.openai import AzureOpenAIChatClient; print('AzureOpenAIChatClient OK')"
python -c "from agent_framework.foundry import FoundryChatClient; print('FoundryChatClient OK')"
python -c "from azure.identity import AzureCliCredential, get_bearer_token_provider; print('azure-identity OK')"
```

Then print the constructor signature (needed if the smoke script fails):

```powershell
python -c "from agent_framework.openai import AzureOpenAIChatClient; import inspect; print(inspect.signature(AzureOpenAIChatClient.__init__))"
python -c "from agent_framework.foundry import FoundryChatClient; import inspect; print(inspect.signature(FoundryChatClient.__init__))"
```

Do **not** install anything if these imports succeed.

If `AzureOpenAIChatClient` import fails, report the traceback and stop the
OpenAI smoke test (Step 5). Do not guess a different class name.

### Step 2 — Azure CLI subscription

```powershell
az account show --query "{name:name, id:id, user:user.name, state:state}" -o json
```

Expected name: `T332 - TCO`.
Expected id: `baa67dbf-45d0-4d84-b662-527186361068`.

If the subscription is wrong:

```powershell
az account set --subscription "T332 - TCO"
az account show --query "{name:name, id:id}" -o json
```

If `az login` is required, tell the human to log in. Do not invent a
workaround.

### Step 3 — list Cognitive Services accounts (Foundry vs classic OpenAI)

This answers: do we have a Foundry project endpoint (`*.services.ai.azure.com`)
or only classic Azure OpenAI (`*.openai.azure.com`)?

```powershell
az cognitiveservices account list --query "[].{name:name, kind:kind, sku:sku.name, endpoint:properties.endpoint, rg:resourceGroup}" -o table
```

Also print JSON so the endpoint strings are complete:

```powershell
az cognitiveservices account list --query "[].{name:name, kind:kind, endpoint:properties.endpoint, rg:resourceGroup}" -o json
```

How to interpret:

- If **any** `endpoint` contains `services.ai.azure.com` → Foundry project
  inference **may** be available. Copy that exact URL into the report as
  `FOUNDRY_PROJECT_ENDPOINT`.
- If you only see `https://pf-t332-openai-use2.openai.azure.com/` (or other
  `*.openai.azure.com`) → classic Azure OpenAI only. That is **OK**. The
  migration will use `AzureOpenAIChatClient`.
- `kind` values you may see: `OpenAI`, `AIServices`, `CognitiveServices`.
  Record them. Do not guess what they mean beyond the endpoint hostname.

Optional portal note (only if CLI shows nothing useful): open
https://ai.azure.com , pick the T332 / TCO project if it exists, Overview
page, copy **Project endpoint**. If the human cannot find a project, write
`NO_FOUNDRY_PROJECT`.

### Step 4 — confirm the smoke-test deployment still exists

```powershell
az cognitiveservices account deployment list -g pf-T332-t-cog -n pf-t332-openai-use2 --query "[].name" -o tsv
```

Confirm this name is in the list:

- `gpt-4o-mini-gs-2024-07-18`

Do **not** paste the entire deployment list into the report. Only say whether
that one name is present, and list any extra **chat** deployments that look
newer than gpt-4o if you want (optional). Do not call gpt-5 / o-series models.

### Step 5 — OpenAI smoke test (required)

Create this file exactly. Path:

`C:\Users\dauba1\Work\maf_smoke.py`

If that folder does not exist, create the file in the current working
directory and report the full path.

File contents (copy exactly):

```python
import asyncio
from azure.identity import AzureCliCredential, get_bearer_token_provider
from agent_framework.openai import AzureOpenAIChatClient

ENDPOINT = "https://pf-t332-openai-use2.openai.azure.com/"
DEPLOYMENT = "gpt-4o-mini-gs-2024-07-18"

token_provider = get_bearer_token_provider(
    AzureCliCredential(),
    "https://cognitiveservices.azure.com/.default",
)

client = AzureOpenAIChatClient(
    endpoint=ENDPOINT,
    deployment_name=DEPLOYMENT,
    ad_token_provider=token_provider,
)

agent = client.as_agent(
    name="Smoke",
    instructions="Reply with exactly: ok",
)

async def main():
    result = await agent.run("ping")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

Then run:

```powershell
python maf_smoke.py
```

**If the constructor fails** with `TypeError` / unexpected keyword:

1. Look at the signature from Step 1.
2. Adjust **only** the keyword names to match the installed package
   (`deployment_name` vs `model`, `ad_token_provider` vs `credential`, etc.).
3. Re-run once.
4. In the report, write the **working constructor keyword names**.

**If it succeeds:** the printed text should contain `ok` (case may differ).
Mark Step 5 PASS. Paste the printed output (it is not a secret).

**If it fails:** paste the full traceback. Common meanings (do not fix unless
the human asks):

| Error text contains | Meaning |
|---|---|
| `CredentialUnavailableError` | `az login` token not usable |
| `401` or `403` | no Cognitive Services User (or equivalent) on `pf-t332-openai-use2` |
| `404` | wrong deployment name |
| `ModuleNotFoundError` | missing import; report it, do not pip install |

### Step 6 — Foundry smoke test (only if Step 3 found a Foundry endpoint)

Skip this entire step if Step 3 did not find a `*.services.ai.azure.com` URL.
Write `SKIP — no Foundry project endpoint`.

If you **did** find one, set the variable then run. Replace the URL with the
exact value from Step 3:

```powershell
$env:FOUNDRY_PROJECT_ENDPOINT = "PASTE_EXACT_URL_HERE"
```

Create `C:\Users\dauba1\Work\maf_foundry_smoke.py`:

```python
import asyncio
import os
from azure.identity import AzureCliCredential
from agent_framework.foundry import FoundryChatClient

client = FoundryChatClient(
    project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    model="gpt-4o-mini-gs-2024-07-18",
    credential=AzureCliCredential(),
)
agent = client.as_agent(name="Smoke", instructions="Reply with exactly: ok")

async def main():
    print(await agent.run("ping"))

if __name__ == "__main__":
    asyncio.run(main())
```

Run:

```powershell
python maf_foundry_smoke.py
```

If the constructor kwargs are wrong, use the Step 1 signature, change only
kwargs, retry once.

If this fails but Step 5 passed, that is OK. Report FAIL for Step 6 and
recommend `AzureOpenAIChatClient`.

### Step 7 — do not install leftover packages

Check whether `azure-ai-evaluation` is installed:

```powershell
pip show azure-ai-evaluation
```

Expected: package **not** found. Leave it that way.

Do **not** run `pip install azure-ai-evaluation`.
Do **not** run `pip install agent-framework` again.
Do **not** create a new conda env.

### Step 8 — optional, low priority: Search reachability

Only if Steps 0–5 all passed and you still have time. Do **not** print keys.

```powershell
az account get-access-token --resource https://search.azure.com --query expiresOn -o tsv
```

If that command works, write `AAD token for Azure Search: OK`.
If it fails, write FAIL and the error. Do not query indexes in this checklist.

### Report template (fill this exactly)

```text
MAF VDI readiness report
Date:
Machine / user:

Step 0 Python version:
Step 0 interpreter path:
Step 1 agent_framework version:
Step 1 AzureOpenAIChatClient import: PASS/FAIL
Step 1 FoundryChatClient import: PASS/FAIL
Step 1 AzureOpenAIChatClient signature:
Step 1 FoundryChatClient signature:
Step 2 subscription name:
Step 2 subscription id:
Step 3 accounts (name, kind, endpoint) — paste table:
Step 3 Foundry endpoint found?: YES/NO
Step 3 FOUNDRY_PROJECT_ENDPOINT (or NO_FOUNDRY_PROJECT):
Step 4 gpt-4o-mini-gs-2024-07-18 present?: YES/NO
Step 5 OpenAI smoke test: PASS/FAIL
Step 5 output or error:
Step 5 working constructor kwargs (if changed):
Step 6 Foundry smoke test: PASS/FAIL/SKIP
Step 6 output or error:
Step 7 azure-ai-evaluation installed?: YES/NO (must be NO)
Step 8 Search AAD token: PASS/FAIL/SKIP

Recommended chat client for migration:
  [ ] AzureOpenAIChatClient  (classic https://pf-t332-openai-use2.openai.azure.com/)
  [ ] FoundryChatClient      (only if Step 6 PASS)

Ready to start a 2-executor MAF slice?: YES/NO
Blockers (if NO):
```

Stop after the report. Do not start writing workflow code. Do not modify the
Prompt Flow repo.

## End of prompt for the VDI agent

