# Agent runbook: Tracker cases on MAF slice 3

You are a **runner**, not a developer. Batch all 36 Tracker cases through the
existing MAF workflow, answer follow-ups if asked, and save artifacts. A human
will compare logs to Prompt Flow Run Log **ID003** later.

## Hard rules

1. **Do not edit** any `.py`, `.yaml`, prompt, or `maf/tracker_cases.json`.
   No `git commit` / `git push`. Do not install packages unless the env cannot
   import `agent_framework` (then stop and report).
2. From the **repository root**, conda env **`maf`**, Python 3.10+.
3. Azure CLI logged in to **T332 - TCO**.
4. Run the batch with **`.\run_slice3_tracker.ps1`**. Do not hand-type
   `python -m maf.slice3` follow-ups in the shell, and do not use
   `Start-Process -ArgumentList` with an unquoted sentence — Windows splits
   `Tie-ins at TP-001...` into extra argv tokens and argparse fails with
   `unrecognized arguments: at TP-001 and TP-002.`
5. Do not write extra markdown “error log” docs. Failures belong in
   `maf/runs/<run-id>/summary.json` and `TC-NNN/turn-NN.stderr.txt`.

## Preconditions (once)

```powershell
az account show --query "{name:name, id:id}" -o json
# name must be T332 - TCO
conda activate maf
python -c "import agent_framework; print('ok')"
```

Wrong subscription: `az account set --subscription "T332 - TCO"`.
No login: `az login`, then stop if that fails.

## How to run

```powershell
Set-Location <repo-root>
conda activate maf
.\run_slice3_tracker.ps1
```

The script creates `maf/runs/YYYYMMDD-HHMM-slice3/` (plus a zip), loops
`TC-001` … `TC-036`. A turn is **done** only when `complete` is true **and**
`route.kind` is `json` (a job pack). If the model asks for an I&E Job Pack
(electric tracing), reply `I&E Job Pack YY-NNNN` — that is the placeholder in
Nur’s ID003 packs. Do not invent tie-in IDs when the deducted prompt says TBD.

Cap is 6 turns per case (`stuck` if still not a pack). One case failing does
not abort the rest unless Azure auth is broken.

## What success looks like

A **pack turn** is `complete=true` **and** `route.kind=json`. Electric tracing
often has `complete=true` with `route.kind=string` (I&E question) — keep going.

TBD tie-ins should **not** ask for TP-001/TP-002. Scope/insulation/diameter
canned replies stay in `Get-FollowUp`. Tee/branch: `Tee replacement. Replace
the pipe section.`

Turn 1 input is the test ID. Later turns are follow-up text, never `TC-00N`
again.

## Artifacts

```text
maf/runs/YYYYMMDD-HHMM-slice3/
  summary.json
  TC-001/history.json  turn-01.json  turn-01.stderr.txt
  TC-002/...
maf/runs/YYYYMMDD-HHMM-slice3.zip
```

`summary.json` is updated after every case. Job pack text stays in
`turn-NN.json` (`answer`), not in the summary.

## Done when

- `summary.json` has `finished_utc` and 36 case rows (or fewer only if auth
  died globally).
- `git status` shows only `maf/runs/...` (gitignored) and no source edits.
- You report: run folder name, Complete / Stuck / Error counts.

Do not compare wording to the Excel Run Log, re-run cases to “improve” packs,
open Azure Portal, or put a Search API key in the environment.
