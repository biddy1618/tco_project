# Internal Azure checklist (do not include in shared zips).

Known facts live in [azure-environment.md](azure-environment.md). When a check
returns a new fact, update that inventory. Do not put workstation hostnames
in the inventory.

**Closed:** classic OpenAI smoke; Search AAD token; Foundry project portal;
`FoundryChatClient` smoke; Foundry account has the three PF deployments
(`gpt-4o-mini-gs-2024-07-18`, `gpt-4o-gs-2024-05-13`,
`text-embedding-ada-002-gs-2`). See inventory §2, §7.

**Open (step 0):** can this identity **push a container image** and
**create a Foundry hosted agent** in
`pf-t332-t-aif-use2-c3-jobpack-project`?

**Human:** paste `azure-environment.md`, then everything under **Prompt**.

---

## Prompt

You are on a Windows machine with conda env `maf` and `az login` on
subscription **T332 - TCO**. Confirm only the unknowns below.

Do **not** install packages. Do **not** install Docker, `azd`, or CLI
extensions. Do **not** `docker login`, `az acr login`, push an image, or
create/update any agent. Do **not** print secrets, passwords, or access
tokens. Do **not** re-test classic `pf-t332-openai-use2` or re-run
`foundry_smoke.py` (already proven).

`az account show` must be **T332 - TCO**
(`baa67dbf-45d0-4d84-b662-527186361068`). If it is not, stop and say so.

Already known (do not rediscover unless a command fails):

- Foundry / AIServices account: `pf-t332-t-aif-use2-c3` (eastus2)
- Foundry project: `pf-t332-t-aif-use2-c3-jobpack-project`
- Account endpoint:
  `https://pf-t332-t-aif-use2-c3.cognitiveservices.azure.com/`
- Group RBAC on the account RG (previous check):
  `pf-T332-ai-services-consumers` → Reader;
  `Chevron AI Services Operator`

Hosted-agent deploy needs **Foundry Project Manager** (or equivalent
data-plane write) on the project, plus an **Azure Container Registry**
this identity can **push** to. Reader on the RG is not enough.

### 1. Who is signed in (names only)

```powershell
az account show --query "{name:name, id:id, user:user.name, tenantId:tenantId}" -o json
```

### 2. Foundry account resource group + ids

```powershell
az resource list --name pf-t332-t-aif-use2-c3 --query "[].{name:name, rg:resourceGroup, type:type, id:id}" -o json
```

Save `rg` as `ACCOUNT_RG` for later steps.

Find the Foundry **project** ARM resource (name may match the project or
sit under the account). Try both:

```powershell
az resource list --name pf-t332-t-aif-use2-c3-jobpack-project --query "[].{name:name, rg:resourceGroup, type:type, id:id}" -o json
az resource list -g ACCOUNT_RG --query "[?contains(type, 'Microsoft.CognitiveServices') || contains(type, 'Microsoft.MachineLearningServices')].{name:name, type:type, id:id}" -o json
```

If the project id is found, save it as `PROJECT_ID`. If not found, write
`PROJECT_ID=NOT_FOUND` and still run the remaining steps on the account
and RG.

### 3. Roles on the account, its RG, and the project

Replace `ACCOUNT_RG` (and `PROJECT_ID` if you have it). Include group
assignments. Names and role titles only — no object ids required.

```powershell
az role assignment list --include-groups --scope (az cognitiveservices account show -n pf-t332-t-aif-use2-c3 --query id -o tsv) --query "[].{principal:principalName, role:roleDefinitionName}" -o table

az role assignment list --include-groups --scope (az group show -n ACCOUNT_RG --query id -o tsv) --query "[].{principal:principalName, role:roleDefinitionName}" -o table
```

If `PROJECT_ID` exists:

```powershell
az role assignment list --include-groups --scope PROJECT_ID --query "[].{principal:principalName, role:roleDefinitionName}" -o table
```

In the report, mark YES/NO whether **this user or a group they belong
to** has any of these role names (current or old Azure AI names count):

- Foundry Project Manager / Azure AI Project Manager
- Foundry User / Azure AI User
- Foundry Owner / Azure AI Owner
- Contributor
- Owner
- AcrPush
- AcrPull
- ACR Contributor / Container Registry Contributor

If the tables are long, paste only rows whose role contains `Foundry`,
`Azure AI`, `ACR`, `Acr`, `Container Registry`, `Contributor`, `Owner`,
`Operator`, or `User`.

### 4. Azure Container Registries in this subscription

```powershell
az acr list --query "[].{name:name, rg:resourceGroup, login:loginServer, sku:sku.name, location:location}" -o table
```

If that returns none, also search the Foundry account RG:

```powershell
az acr list -g ACCOUNT_RG -o table
az resource list -g ACCOUNT_RG --resource-type Microsoft.ContainerRegistry/registries --query "[].{name:name, id:id}" -o json
```

If still none: write `NO_ACR` and skip step 5. Do **not** create a
registry.

If one or more exist: list every `name` + `loginServer`. Prefer a
registry in `ACCOUNT_RG` or with `t332` / `tco` / `foundry` / `aif` in
the name; if none match, list all (cap at 10).

### 5. Can this identity push? (no actual push)

For **each** registry from step 4 (max 3 if there are many — pick the
preferred one first):

```powershell
az acr show -n REGISTRY_NAME --query "{name:name, rg:resourceGroup, adminUserEnabled:adminUserEnabled, login:loginServer}" -o json

az role assignment list --include-groups --scope (az acr show -n REGISTRY_NAME --query id -o tsv) --query "[].{principal:principalName, role:roleDefinitionName}" -o table
```

Then a **dry** permission check (does not upload an image):

```powershell
az acr login -n REGISTRY_NAME
```

- If `az acr login` succeeds: write `ACR_LOGIN=PASS` for that registry.
  Do **not** `docker push`.
- If it fails: paste the **error message only** (no token). Typical
  403/`authorization` = no push/login role.

Optional (skip if it errors): `az acr repository list -n REGISTRY_NAME -o table`
proves data-plane list; empty is OK.

### 6. gpt-4o on the Foundry account (needed for later host tests)

Replace `ACCOUNT_RG`:

```powershell
az cognitiveservices account deployment list -g ACCOUNT_RG -n pf-t332-t-aif-use2-c3 --query "[].{name:name, model:properties.model.name}" -o table
```

YES/NO for:

- `gpt-4o-mini-gs-2024-07-18` (already used in smoke; confirm still there)
- `gpt-4o-gs-2024-05-13` (classic OpenAI name for ask_or_finalize)

### Report

```text
Subscription / user (from step 1):
Foundry account RG:
Project ARM type + id (or NOT_FOUND):

Foundry Project Manager (or Azure AI Project Manager)?: YES/NO
Foundry User (or Azure AI User)?: YES/NO
Contributor/Owner on account RG?: YES/NO

ACR list (name, loginServer, rg) or NO_ACR:
Preferred ACR for hosted-agent images:
az acr login on preferred ACR: PASS/FAIL/SKIP
ACR roles on preferred registry (names only):

gpt-4o-mini-gs-2024-07-18 on Foundry account?: YES/NO
gpt-4o-gs-2024-05-13 on Foundry account?: YES/NO

Ready to push an image (ACR login PASS + AcrPush or Contributor)?: YES/NO
Ready to create a hosted agent in this project (Project Manager or Foundry User)?: YES/NO
Blocker if either is NO (one sentence):
```

Stop. Do not change `maf/` code, do not create resources, do not install
Docker. The human will copy facts into `docs/azure-environment.md`.
