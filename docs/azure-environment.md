# Azure + VDI environment inventory

Living facts about the corporate VDI, Azure subscription, connections, and
indexes this project uses. **No secrets.** Update this file when a check
changes a value; do not duplicate it into prompt files.

Related:

- [questions-for-azure.md](questions-for-azure.md) — copy-paste prompts only
- [flow-structure.md](flow-structure.md) — Prompt Flow DAG and logic audit
- `flow.dag.yaml` — runtime wiring (endpoints, connection names, deployments)

Last updated: 2026-08-26.

---

## 1. Corporate VDI (MAF workstation)

| Item | Value | Status |
|---|---|---|
| Host | Windows VDI, user `dauba1` | confirmed |
| Work dir seen | `C:\Users\dauba1\Work` | confirmed |
| Conda env | `maf` (`conda activate maf`) | confirmed |
| Python | 3.11.15 (meets MAF's 3.10+ requirement) | confirmed |
| Package index | `artifactory.chevron.com/artifactory/api/pypi` | confirmed |
| Index paths | `pypi-local/simple`, `pypi-local-dev/simple`, `pypi/simple` | confirmed |
| Azure CLI | installed; `az login` already done for this user | confirmed |
| `azure-ai-evaluation` | **not** installed — do not install until parity-check phase | confirmed |

There is **no** `maf new` / `az maf create` CLI. A MAF “project” is a Python
package that imports `agent_framework`.

### Installed MAF packages (conda env `maf`, 2026-08-26)

| Package | Version |
|---|---|
| `agent-framework` | 1.14.0 |
| `agent-framework-core` | 1.14.0 |
| `agent-framework-openai` | 1.13.0 |
| `agent-framework-foundry` | 1.11.0 |
| `agent-framework-azure-ai-search` | 1.0.0b260813 |
| `azure-identity` | 1.25.3 |
| `azure-ai-projects` | 2.3.0 |
| `azure-search-documents` | 12.0.0 |

Many other `agent-framework-*` extras are already present. Do **not** pip
install more of them.

### MAF chat-client API (this installed version)

`agent-framework` **1.14.0 does not export `AzureOpenAIChatClient`**. That
class was removed. Use:

| Class | Module | Azure OpenAI API |
|---|---|---|
| `OpenAIChatClient` | `agent_framework.openai` | Responses (try first) |
| `OpenAIChatCompletionClient` | `agent_framework.openai` | Chat Completions (fallback) |
| `FoundryChatClient` | `agent_framework.foundry` | Foundry project endpoint only |

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
| Account state | Enabled |
| Signed-in user | `Dauren.Baitursyn@tengizchevroil.com` |
| Auth type | Azure CLI user (`az login`) |

`az account show` on the VDI already had this subscription as default.

### Rights we have actually proven

| Access | Proven? | How |
|---|---|---|
| List OpenAI deployments on `pf-t332-openai-use2` | **yes** | `az cognitiveservices account deployment list` returned dozens of names |
| Call a chat completion as this user | **not yet** | Q4 Step 5 smoke test |
| Foundry project (`*.services.ai.azure.com`) | **unknown** | Q4 Step 3 |
| Azure AI Search as AAD (no key) | **not yet** | Q4 Step 8 |
| Role name on the OpenAI resource (e.g. Cognitive Services User) | **inferred only** | listing deployments succeeded; inference still untested |

Do not assume Contributor. Listing deployments ≠ permission to invoke a model.

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
| Kind | classic Azure OpenAI (`*.openai.azure.com`), not Foundry project host |

This is the endpoint Prompt Flow already uses (`api_base` on the `nde` node
and the `pf-openai-use2-id-auth` connection).

### Azure AI Search

| Item | Value |
|---|---|
| Endpoint | `https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net` |
| API version used by the flow | `2023-11-01` (confirmed working 2026-08-25) |
| Indexes this flow uses | `ndeee`, `wps-diain` |
| Semantic config (`ndeee`) | `ndeee-semantic-configuration` — exists |
| Semantic config (`wps-diain`) | `wps-diain-semantic-configuration` — exists |

`flow.dag.yaml` still has a **hardcoded Search API key** on `wps_api` (legacy
export). Do not copy it here. Rotate it and move it to a connection / env var.

---

## 4. Model deployments

Resource: `pf-t332-openai-use2` / RG `pf-T332-t-cog`. Listed from the VDI on
2026-08-26. The flow only needs the three below.

| Role in this project | Deployment name | Use |
|---|---|---|
| Smoke test / cheap chat | `gpt-4o-mini-gs-2024-07-18` | Q4 Step 5; PF `spell_check` |
| Production chat | `gpt-4o-gs-2024-05-13` | PF `ask_or_finalize`, `final` |
| Embeddings | `text-embedding-ada-002-gs-2` | PF `nde` mlindex embeddings |

Many other deployments exist on the same resource (gpt-4o / gpt-4.1 / gpt-5 /
o-series, transcribe, TTS, image). **Do not call them** for this project’s
smoke test or first MAF slice.

---

## 5. Search indexes (answered 2026-08-25)

Queried live with `api-version=2023-11-01` and an AAD token, subscription
**T332 - TCO**. There is **no** separate material/CS-SS index; material lives
inside `ndeee`.

### `ndeee` (NDE / PMI / material)

Retrievable fields that matter:

| Field | Type | Retrievable | Searchable |
|---|---|---|---|
| `line_class` | Edm.String | yes | yes |
| `pmi_percent` | Edm.String | yes | no |
| `content` | Edm.String | yes | no |
| `material` | Edm.String | **no** | no |
| `nde_percent` | Edm.String | **no** | no |

Keyword search must target `line_class` (the flow does). `content` is a full
sentence, not a bare line class. Sample (`150A20`, `top=1`):

```json
{
  "line_class": "150A20",
  "pmi_percent": "100",
  "content": "Pipe line class 150A20. Design code ASME B31.3. Design temperature range -40 / 200 deg C. Material Alloy 20. PMI 100.0."
}
```

Implications already applied in code: map `nde` `field_mapping.content` to
`content`; parse PMI as a number from the string `"100"`; parse material from
the `content` sentence.

### `wps-diain` (WPS / PWHT)

| Field | Type |
|---|---|
| `line_class` | Edm.String |
| `dia_in1` | Edm.Double |
| `dia_in2` | Edm.Double |
| `pwht` | Edm.String |

`pwht` values across 266 docs: `N` (128), `Y` (103), blank (18),
`N see Note (7)` (17). Blank is treated as `"No"` in `pf_jobpack/pwht.py` so
the field-weld NDE line still emits.

### Other indexes

33 indexes exist on the service. Only `ndeee` and `wps-diain` are used by this
flow. Full list from 2026-08-25 is in git history of the old answers section
if needed; do not query the others.

---

## 6. Still unknown / next checks

Tracked by [questions-for-azure.md](questions-for-azure.md):

- [ ] Foundry project endpoint (`*.services.ai.azure.com`) exists or not
- [ ] `OpenAIChatClient` (or Completions fallback) can complete a chat as
      this user against `gpt-4o-mini-gs-2024-07-18`
- [ ] AAD token for `https://search.azure.com` works from the VDI
- [ ] Exact RBAC roles on `pf-t332-openai-use2` and the Search service

After Q4 comes back, update this file (not the questions file) with the
working client name and any Foundry URL.
