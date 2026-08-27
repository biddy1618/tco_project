# Azure environment

Subscription, connections, deployments, and Search indexes this project uses.
**No secrets.** Update this file when a check changes a value.

Related:

- [flow-structure.md](flow-structure.md) — Prompt Flow DAG and logic audit
- `flow.dag.yaml` — runtime wiring (endpoints, connection names, deployments)
- [maf/README.md](../maf/README.md) — Agent Framework slices

Last updated: 2026-08-26.

---

## 1. Runtime for MAF slices

| Item | Value |
|---|---|
| Python | 3.10+ (3.11 verified) |
| Packages | `maf/requirements.txt` (`agent-framework==1.14.0`, `azure-identity`) |
| Package index | `artifactory.chevron.com/artifactory/api/pypi` (`pypi-local/simple`, `pypi-local-dev/simple`, `pypi/simple`) |
| Azure CLI | `az login`; subscription **T332 - TCO** |
| `azure-ai-evaluation` | not required until a later parity-check phase |

There is no `maf new` / `az maf create` CLI. A MAF project is a Python package
that imports `agent_framework`.

### MAF chat-client API (`agent-framework` 1.14.0)

This version does **not** export `AzureOpenAIChatClient`. Use:

| Class | Module | API |
|---|---|---|
| `OpenAIChatClient` | `agent_framework.openai` | Responses (verified 2026-08-26) |
| `OpenAIChatCompletionClient` | `agent_framework.openai` | Chat Completions (fallback) |
| `FoundryChatClient` | `agent_framework.foundry` | Foundry project endpoint only — **not used here** |

Force Azure routing with `azure_endpoint=` + `credential=AzureCliCredential()`
from `azure.identity.aio`. Pass the **deployment name** as `model=`. Do not
rely on env vars alone (`OPENAI_API_KEY` would send traffic to public OpenAI).

---

## 2. Azure identity and subscription

| Item | Value |
|---|---|
| Cloud | `AzureCloud` |
| Tenant | Chevron (`chevron.onmicrosoft.com`) |
| Tenant id | `fd799da1-bfc1-4234-a91c-72b3a1cb9e26` |
| Subscription name | **T332 - TCO** |
| Subscription id | `baa67dbf-45d0-4d84-b662-527186361068` |
| Auth | Azure CLI (`az login`) + `AzureCliCredential` |

### Access proven

| Access | Proven? |
|---|---|
| List OpenAI deployments on `pf-t332-openai-use2` | yes |
| Invoke `gpt-4o-mini-gs-2024-07-18` via `OpenAIChatClient` | yes |
| Foundry project (`*.services.ai.azure.com`) | **none** — classic Azure OpenAI only |
| AAD token for Azure AI Search | yes |
| Exact RBAC role names | not listed (invoke already works) |

---

## 3. Azure resources this flow uses

### Azure Machine Learning / Prompt Flow workspace

From `flow.dag.yaml` connection resource IDs:

| Item | Value |
|---|---|
| Subscription | `baa67dbf-45d0-4d84-b662-527186361068` |
| Resource group | `pf-T332-t-dsws` |
| Workspace | `pf-T332-dsws-test-euw1-tc-cvx` |
| OpenAI connection name | `pf-openai-use2-id-auth` |
| Search connection name | `pf-t332-t-cog` |

### Azure OpenAI (classic)

| Item | Value |
|---|---|
| Resource group | `pf-T332-t-cog` |
| Resource name | `pf-t332-openai-use2` |
| Endpoint | `https://pf-t332-openai-use2.openai.azure.com/` |
| Kind | classic Azure OpenAI (`*.openai.azure.com`), not a Foundry project host |

Prompt Flow uses the same endpoint via `pf-openai-use2-id-auth`.

### Azure AI Search

| Item | Value |
|---|---|
| Endpoint | `https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net` |
| API version | `2023-11-01` |
| Indexes | `ndeee`, `wps-diain` |
| Semantic config (`ndeee`) | `ndeee-semantic-configuration` |
| Semantic config (`wps-diain`) | `wps-diain-semantic-configuration` |

`flow.dag.yaml` still has a hardcoded Search API key on `wps_api`. Do not copy
it here. Rotate it and move it to a connection / environment variable.

---

## 4. Model deployments

Resource: `pf-t332-openai-use2` / RG `pf-T332-t-cog`. The flow only needs:

| Role | Deployment name | Use |
|---|---|---|
| Cheap chat | `gpt-4o-mini-gs-2024-07-18` | PF / MAF `spell_check` |
| Production chat | `gpt-4o-gs-2024-05-13` | `ask_or_finalize`, `final` |
| Embeddings | `text-embedding-ada-002-gs-2` | PF `nde` mlindex embeddings |

Other deployments exist on the same resource. Do not call them for this POC.

---

## 5. Search indexes (2026-08-25)

Queried live with `api-version=2023-11-01`. There is **no** separate
material/CS-SS index; material lives inside `ndeee`.

### `ndeee` (NDE / PMI / material)

| Field | Type | Retrievable | Searchable |
|---|---|---|---|
| `line_class` | Edm.String | yes | yes |
| `pmi_percent` | Edm.String | yes | no |
| `content` | Edm.String | yes | no |
| `material` | Edm.String | **no** | no |
| `nde_percent` | Edm.String | **no** | no |

Keyword search must target `line_class`. `content` is a full sentence. Sample
(`150A20`, `top=1`):

```json
{
  "line_class": "150A20",
  "pmi_percent": "100",
  "content": "Pipe line class 150A20. Design code ASME B31.3. Design temperature range -40 / 200 deg C. Material Alloy 20. PMI 100.0."
}
```

Code implications (already applied): map `nde` `field_mapping.content` to
`content`; parse PMI from the string `"100"`; parse material from `content`.

### `wps-diain` (WPS / PWHT)

| Field | Type |
|---|---|
| `line_class` | Edm.String |
| `dia_in1` | Edm.Double |
| `dia_in2` | Edm.Double |
| `pwht` | Edm.String |

`pwht` across 266 docs: `N` (128), `Y` (103), blank (18), `N see Note (7)` (17).
Blank is treated as `"No"` in `pf_jobpack/pwht.py`.

---

## 6. Still open

- Exact RBAC role names on the OpenAI and Search resources
- MAF slice 3 (Search lookups + job-pack `template` + `final`)

---

## 7. Microsoft Foundry target project (2026-08-27)

This is the Foundry project the browser opened for
`pf-t332-t-aif-use2-c3-jobpack-project`.

| Item | Value | Explicitly checked |
|---|---|---|
| Portal URL | `https://ai.azure.com/nextgen/r/uqZ9v0XQTYS2YlJxhjYQaA,pf-T332-t-aif-c3,,pf-t332-t-aif-use2-c3,pf-t332-t-aif-use2-c3-jobpack-project/build/agents?tid=fd799da1-bfc1-4234-a91c-72b3a1cb9e26` | browser opened successfully |
| Page title | `Microsoft Foundry` | browser snapshot |
| Project name | `pf-t332-t-aif-use2-c3-jobpack-project` | browser snapshot |
| Portal area reached | `build/agents` | browser snapshot |
| Portal nav visible | Agents, Deployments, Services, Tools, Knowledge, Memory, Guardrails, Data, Evaluations | browser snapshot |
| Portal note shown | This project logs traces; some members with Log Analytics Reader in AppInsights may be able to view user data | browser snapshot |
| Target resource name | `pf-t332-t-aif-use2-c3` | `az resource show` |
| Target resource type | `Microsoft.CognitiveServices/accounts` | `az resource show` |
| Target resource kind | `AIServices` | `az resource show` |
| Target resource location | `eastus2` | `az resource show` |
| Direct RBAC for `Dauren.Baitursyn@tengizchevroil.com` | none returned | `az role assignment list --assignee` |
| Group RBAC on target RG | `pf-T332-ai-services-consumers` -> `Reader`; `Chevron AI Services Operator` | `az role assignment list --include-groups` |
| Source workspace RBAC | `pf-T332-dsws-tc-amlop` -> `Chevron Limited AML Operator` | `az role assignment list` on the source workspace |
