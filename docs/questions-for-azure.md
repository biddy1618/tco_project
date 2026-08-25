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
