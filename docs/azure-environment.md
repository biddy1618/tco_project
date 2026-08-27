# Azure environment

Subscription, connections, deployments, and Search indexes this project uses.
**No secrets.** Update this file when a check changes a value.

Related:

- [flow-structure.md](flow-structure.md) — Prompt Flow DAG and logic audit
- `flow.dag.yaml` — runtime wiring (endpoints, connection names, deployments)
- [maf/README.md](../maf/README.md) — Agent Framework slices

Last updated: 2026-08-27.

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
| `FoundryChatClient` | `agent_framework.foundry` | **MAF default** (verified invoke 2026-08-27) |
| `OpenAIChatClient` | `agent_framework.openai` | Classic Azure OpenAI fallback if `AZURE_OPENAI_ENDPOINT` is set |
| `OpenAIChatCompletionClient` | `agent_framework.openai` | Chat Completions (unused) |

Default Foundry endpoint:
`https://pf-t332-t-aif-use2-c3.cognitiveservices.azure.com/`.
`credential=AzureCliCredential()` from `azure.identity.aio`. Pass the
**deployment name** as `model=`. Do not rely on `OPENAI_API_KEY` alone.

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
| Invoke `gpt-4o-mini-gs-2024-07-18` via `OpenAIChatClient` (classic) | yes |
| Invoke `gpt-4o-mini-gs-2024-07-18` via `FoundryChatClient` | yes |
| List deployments on Foundry account `pf-t332-t-aif-use2-c3` | yes (2026-08-27) |
| Foundry project (`*.services.ai.azure.com`) on the classic OpenAI path | **none** |
| AAD token for Azure AI Search | yes |
| Exact RBAC role names | not listed (invoke already works) |

Note: the Foundry check above is for the classic OpenAI resource path. A
separate Foundry-backed project is documented in section 7 below.

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

This is a separate Foundry-backed project for `pf-t332-t-aif-use2-c3-jobpack-project`.
It is not the classic Azure OpenAI resource documented above.

| Item | Value | Explicitly checked |
|---|---|---|
| Portal URL | `https://ai.azure.com/nextgen/r/uqZ9v0XQTYS2YlJxhjYQaA,pf-T332-t-aif-c3,,pf-t332-t-aif-use2-c3,pf-t332-t-aif-use2-c3-jobpack-project/build/agents?tid=fd799da1-bfc1-4234-a91c-72b3a1cb9e26` | browser opened successfully |
| Page title | `Microsoft Foundry` | browser snapshot |
| Project name | `pf-t332-t-aif-use2-c3-jobpack-project` | browser snapshot |
| Portal area reached | `build/agents` | browser snapshot |
| Portal nav visible | Agents, Deployments, Services, Tools, Knowledge, Memory, Guardrails, Data, Evaluations | browser snapshot |
| Portal note shown | This project logs traces; some members with Log Analytics Reader in AppInsights may be able to view user data | browser snapshot |
| Account endpoint | `https://pf-t332-t-aif-use2-c3.cognitiveservices.azure.com/` | `az cognitiveservices account show` |
| Target resource name | `pf-t332-t-aif-use2-c3` | `az resource show` |
| Target resource type | `Microsoft.CognitiveServices/accounts` | `az resource show` |
| Target resource kind | `AIServices` | `az resource show` |
| Target resource location | `eastus2` | `az resource show` |
| Direct RBAC for `Dauren.Baitursyn@tengizchevroil.com` | none returned | `az role assignment list --assignee` |
| Group RBAC on target RG | `pf-T332-ai-services-consumers` -> `Reader`; `Chevron AI Services Operator` | `az role assignment list --include-groups` |
| Source workspace RBAC | `pf-T332-dsws-tc-amlop` -> `Chevron Limited AML Operator` | `az role assignment list` on the source workspace |
| `FoundryChatClient` smoke test | PASS | `foundry_smoke.py` returned `ok` |

Smoke test details:

- Client: `FoundryChatClient`
- Endpoint used: `https://pf-t332-t-aif-use2-c3.cognitiveservices.azure.com/`
- Deployment used: `gpt-4o-mini-gs-2024-07-18`
- Result: `ok`

### Deployments on this Foundry account (2026-08-27)

Listed with `az cognitiveservices account deployment list` on
`pf-t332-t-aif-use2-c3` / RG `pf-T332-t-aif-c3`. The three Prompt Flow names
are present:

| Deployment name | Present |
|---|---|
| `gpt-4o-mini-gs-2024-07-18` | yes |
| `gpt-4o-gs-2024-05-13` | yes |
| `text-embedding-ada-002-gs-2` | yes |

Other chat deployments on the same account (not used by this POC):
`gpt-4o-gs-2024-08-06`, `gpt-4o-gs-2024-11-20`, `gpt-4o-gb-2024-05-13`,
`gpt-4o-gb-2024-08-06`, `gpt-4o-gb-2024-11-20`, `o3-mini-gs-2025-01-31`,
`o3-mini-gb-2025-01-31`, `o3-gs-2025-04-16`, `o3-gb-2025-04-16`,
`o4-mini-gs-2025-04-16`, `o4-mini-gb-2025-04-16`, `gpt-4_1-gs-2025-04-14`,
`gpt-4_1-gb-2025-04-14`, `gpt-4_1-mini-gs-2025-04-14`,
`gpt-4_1-mini-gb-2025-04-14`.

MAF uses the same three PF names on this Foundry endpoint. Hosted-agent
container publish is a separate, blocked path (see §8).

What this means, based only on what was checked:

- The Foundry project page is reachable in the browser.
- The three Prompt Flow deployment names exist on this Foundry account
  (`gpt-4o-mini`, `gpt-4o`, embeddings).
- The AIServices account endpoint is reachable from Python with `FoundryChatClient`.
- Your access to the target project is group-based, not a direct user RBAC assignment.
- The current project is backed by an `AIServices` account, not a git repository.
- I did not check any git-backed sync or import feature, so "push code" is not something I can confirm here; the checked path is portal/project asset migration, not a repo push.

---

## 8. Hosted-agent readiness check (2026-08-27)

This section answers the remaining open question: can this identity push a
container image and create a Foundry hosted agent in
`pf-t332-t-aif-use2-c3-jobpack-project`?

### Project ARM resource

| Item | Value | Explicitly checked |
|---|---|---|
| Project ARM id | `/subscriptions/baa67dbf-45d0-4d84-b662-527186361068/resourceGroups/pf-T332-t-aif-c3/providers/Microsoft.CognitiveServices/accounts/pf-t332-t-aif-use2-c3/projects/pf-t332-t-aif-use2-c3-jobpack-project` | `az resource list` |
| Project ARM type | `Microsoft.CognitiveServices/accounts/projects` | `az resource list` |

### Project RBAC

| Item | Value | Explicitly checked |
|---|---|---|
| Project role assignment | `pf-t332-t-aif-use2-c3-jobpack-project-mgmt` -> `Chevron Azure AI User` | `az role assignment list` |
| Project-management group members | `Data Foundation Data Science and ML Operations`; `pf-t332-t-aif-use2-c3-jobpack-project-consumers` | `az ad group member list` |
| Project consumers group members | `Dauren.Baitursyn@tengizchevroil.com`; `Nurmukhambet.Izimgali@tengizchevroil.com` | `az ad group member list` |

### ACR / image push

| Item | Value | Explicitly checked |
|---|---|---|
| ACR inventory in subscription | no ACR found | `az acr list` |
| ACR inventory in target RG | no ACR found | `az acr list -g pf-T332-t-aif-c3` |

What this means, based only on what was checked:

- The identity is covered by the project-management access path through the
  nested project consumers group.
- The project has `Chevron Azure AI User`, not a `Project Manager` or `Owner`
  role.
- There is no Azure Container Registry available in the subscription or the
  target resource group, so there is nowhere to push a hosted-agent image.
- Ready to push an image: **NO**.
- Ready to create a hosted agent in this project: **NO** (blocked by missing
  ACR/image-push target, and no project-manager role was found).

---

## 9. Portal-visible ACRs checked from the VDI (2026-08-27)

These are the registries visible in the Azure portal screenshot that were
checked directly with Azure CLI. They are **not** in the T332 subscription.

### `cdmacr`

| Item | Value | Explicitly checked |
|---|---|---|
| Subscription | `T101 - IT Foundation` | `az acr list --subscription` |
| Resource group | `cdm-t101-20210831` | `az acr show` |
| Login server | `cdmacr.azurecr.io` | `az acr show` |
| SKU | `Standard` | `az acr show` |
| Admin user | `false` | `az acr show` |
| ACR login token test | PASS (token issued) | `az acr login --expose-token` |
| Registry-scope RBAC for this user or matching groups | none found | `az role assignment list` + membership check |

### `pfs019taifusscc3acr`

| Item | Value | Explicitly checked |
|---|---|---|
| Subscription | `S019 - Tiger Teams Sandbox with Sub Level Access` | `az acr list --subscription` |
| Resource group | `pf-S019-t-aif-c3` | `az acr show` |
| Login server | `pfs019taifusscc3acr.azurecr.io` | `az acr show` |
| SKU | `Basic` | `az acr show` |
| Admin user | `true` | `az acr show` |
| ACR login token test | PASS (token issued) | `az acr login --expose-token` |
| Registry-scope `AcrPush` assignment | present, but not tied to the signed-in user in the membership check | `az role assignment list` + `az ad user get-member-groups` |

What this means, based only on what was checked:

- The portal-visible registries exist and the identity can obtain ACR login
  tokens for both.
- `cdmacr` does not show a push-capable registry-scope assignment for this
  identity or its matching groups.
- `pfs019taifusscc3acr` has an `AcrPush` assignment, but the signed-in user was
  not found in the matching membership check, so push access for this identity
  is **not proven**.
- These registries are in different subscriptions from the Foundry target, so
  they could be used as an image store only if the identity also has the right
  push path and the hosted-agent workflow accepts an external ACR.
