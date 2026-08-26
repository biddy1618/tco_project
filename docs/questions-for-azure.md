# Open checks for the VDI agent

Known facts live in [azure-environment.md](azure-environment.md). Do not
repeat them here. When a check returns a new fact, update the inventory.

**Closed (do not re-ask):** Q1–Q3 search schemas and the three flow
deployments — see inventory §4–§5. VDI Python 3.11 / conda `maf` / Artifactory /
`az account` on **T332 - TCO** / deployment list — inventory §1–§4.

**Human:** paste `azure-environment.md`, then everything under **Prompt**.

---

## Prompt

You are on the corporate Windows VDI. Confirm only the unknowns below.
Use the pasted inventory for env name, endpoints, and class names. Do not
install packages. Do not print secrets. Do not re-list deployments.

`conda activate maf` first.

### 1. Foundry endpoint or classic OpenAI only?

```powershell
az cognitiveservices account list --query "[].{name:name, kind:kind, endpoint:properties.endpoint, rg:resourceGroup}" -o json
```

If any endpoint contains `services.ai.azure.com`, copy that URL as
`FOUNDRY_PROJECT_ENDPOINT`. Otherwise write `NO_FOUNDRY_PROJECT`.

### 2. Can this user call a chat deployment?

Write `C:\Users\dauba1\Work\maf_smoke.py` and run `python maf_smoke.py`.
Do **not** import `AzureOpenAIChatClient` (removed in 1.14.0).

```python
import asyncio
from azure.identity.aio import AzureCliCredential
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(
    model="gpt-4o-mini-gs-2024-07-18",
    azure_endpoint="https://pf-t332-openai-use2.openai.azure.com/",
    credential=AzureCliCredential(),
)
agent = client.as_agent(name="Smoke", instructions="Reply with exactly: ok")

async def main():
    print(await agent.run("ping"))

asyncio.run(main())
```

- PASS if the output contains `ok` → working client `OpenAIChatClient`.
- If the error is about Responses / `/v1/responses` / api-version: retry once
  with `OpenAIChatCompletionClient` instead of `OpenAIChatClient` (same kwargs).
  PASS → working client `OpenAIChatCompletionClient`.
- Any other error: FAIL, paste the traceback. Stop.

### 3. Foundry client — only if §1 found a URL

Skip if `NO_FOUNDRY_PROJECT`. Otherwise:

```python
import asyncio, os
from azure.identity import AzureCliCredential
from agent_framework.foundry import FoundryChatClient

os.environ["FOUNDRY_PROJECT_ENDPOINT"] = "PASTE_URL_FROM_STEP_1"
client = FoundryChatClient(
    project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    model="gpt-4o-mini-gs-2024-07-18",
    credential=AzureCliCredential(),
)
agent = client.as_agent(name="Smoke", instructions="Reply with exactly: ok")
print(asyncio.run(agent.run("ping")))
```

PASS / FAIL / SKIP.

### 4. Optional: Search AAD token (no queries)

Only if §2 passed:

```powershell
az account get-access-token --resource https://search.azure.com --query expiresOn -o tsv
```

### Report

```text
Foundry endpoint: <URL or NO_FOUNDRY_PROJECT>
Chat smoke: PASS/FAIL
Working client: OpenAIChatClient / OpenAIChatCompletionClient / NONE
Chat output or error:
Foundry smoke: PASS/FAIL/SKIP
Search AAD token: PASS/FAIL/SKIP
Ready for a 2-executor MAF slice?: YES/NO
```

Stop. Do not write workflow code. The human will copy new facts into
`docs/azure-environment.md`.
