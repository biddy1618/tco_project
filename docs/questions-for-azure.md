# Internal Azure checklist (do not include in shared zips).

Known facts live in [azure-environment.md](azure-environment.md). When a check
returns a new fact, update that inventory. Do not put workstation hostnames
in the inventory.

**Closed:** classic OpenAI smoke (`OpenAIChatClient` on
`pf-t332-openai-use2`), Search AAD token, portal open of Foundry project
`pf-t332-t-aif-use2-c3-jobpack-project`. See inventory §2 and §7.

**Open:** can we **invoke** that Foundry/AIServices resource from Python?

**Human:** paste `azure-environment.md`, then everything under **Prompt**.

---

## Prompt

You are on a Windows machine with conda env `maf` and `az login` on
**T332 - TCO**. Confirm only the unknowns below. Do not install packages.
Do not print secrets or access tokens. Do not re-test classic
`pf-t332-openai-use2` (already proven).

`conda activate maf` first.

Resource already identified:

- Account: `pf-t332-t-aif-use2-c3` (kind `AIServices`, eastus2)
- Foundry project: `pf-t332-t-aif-use2-c3-jobpack-project`

### 1. Project / account endpoint

```powershell
az cognitiveservices account show -n pf-t332-t-aif-use2-c3 --query "{name:name, kind:kind, endpoint:properties.endpoint, rg:resourceGroup, location:location}" -o json
az cognitiveservices account list --query "[?kind=='AIServices' || contains(properties.endpoint, 'services.ai.azure.com')].{name:name, kind:kind, endpoint:properties.endpoint, rg:resourceGroup}" -o json
```

Copy the **exact** `endpoint` string. Prefer a URL containing
`services.ai.azure.com`. If only `cognitiveservices.azure.com` or
`openai.azure.com` appears, still paste it.

Optional (portal): Foundry project **Overview** → copy **Project endpoint**.
If it differs from the CLI endpoint, paste **both**.

### 2. Resource group name

```powershell
az resource list --name pf-t332-t-aif-use2-c3 --query "[].{name:name, rg:resourceGroup, type:type}" -o json
```

### 3. Deployments on the Foundry / AIServices account

Replace `RESOURCE_GROUP` with the RG from step 2:

```powershell
az cognitiveservices account deployment list -g RESOURCE_GROUP -n pf-t332-t-aif-use2-c3 --query "[].{name:name, model:properties.model.name, version:properties.model.version}" -o table
```

If that command 404s, try:

```powershell
az cognitiveservices account deployment list -g RESOURCE_GROUP -n pf-t332-t-aif-use2-c3 -o table
```

In the report, say whether these names exist (YES/NO):

- `gpt-4o-mini-gs-2024-07-18`
- `gpt-4o-gs-2024-05-13`
- `text-embedding-ada-002-gs-2`

Also list **up to 10** other **chat** deployment names (skip image/whisper/tts).

If zero deployments: write `NO_DEPLOYMENTS` and skip step 4.

### 4. FoundryChatClient smoke test (required if step 1 has a URL)

Write `foundry_smoke.py` in the current directory. Use the **endpoint from
step 1**. For `model=`, use `gpt-4o-mini-gs-2024-07-18` if it exists in
step 3; otherwise the first chat deployment from step 3.

Do **not** import `AzureOpenAIChatClient`.

```python
import asyncio
from azure.identity.aio import AzureCliCredential
from agent_framework.foundry import FoundryChatClient

ENDPOINT = "PASTE_ENDPOINT_FROM_STEP_1"
DEPLOYMENT = "PASTE_DEPLOYMENT_FROM_STEP_3"

client = FoundryChatClient(
    project_endpoint=ENDPOINT,
    model=DEPLOYMENT,
    credential=AzureCliCredential(),
)
agent = client.as_agent(name="Smoke", instructions="Reply with exactly: ok")

async def main():
    print(await agent.run("ping"))

asyncio.run(main())
```

Then: `python foundry_smoke.py`

- If constructor `TypeError`: print
  `from agent_framework.foundry import FoundryChatClient; import inspect; print(inspect.signature(FoundryChatClient.__init__))`
  then retry **once** with matching kwargs only (`endpoint` vs
  `project_endpoint`, sync `AzureCliCredential` from `azure.identity` if
  `aio` fails).
- PASS if output contains `ok`.
- FAIL: paste the **full traceback**. Do not guess a fix.
  401/403 = likely missing invoke role. 404 = wrong endpoint or deployment.

### 5. Optional: who can invoke (names only, no tokens)

```powershell
az role assignment list --scope (az cognitiveservices account show -n pf-t332-t-aif-use2-c3 --query id -o tsv) --include-groups --query "[].{principal:principalName, role:roleDefinitionName}" -o table
```

If too long, paste only rows whose role contains `OpenAI`, `Cognitive`,
`AI User`, `AI Developer`, or `Contributor`.

### Report

```text
Account endpoint:
Project endpoint (portal, if different):
Resource group:
gpt-4o-mini-gs-2024-07-18 on this account?: YES/NO
gpt-4o-gs-2024-05-13 on this account?: YES/NO
text-embedding-ada-002-gs-2 on this account?: YES/NO
Other chat deployments (max 10):
FoundryChatClient smoke: PASS/FAIL/SKIP
Smoke deployment used:
Smoke output or error:
Invoke-related role names (optional):
Ready to point maf/client.py at Foundry?: YES/NO
```

Stop. Do not change `maf/` code. The human will copy facts into
`docs/azure-environment.md`.
