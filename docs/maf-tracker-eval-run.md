# Agent runbook: Tracker cases on MAF slice 3

You are a **runner**, not a developer. Run all 36 Tracker cases through the
existing MAF workflow, answer follow-up questions if the flow asks, and **save
artifacts**. Do not change product code. A human will compare your logs to
Prompt Flow Run Log **ID003** later.

## Hard rules

1. **Do not edit, format, or generate** any `.py`, `.yaml`, prompt, or
   `maf/tracker_cases.json`. No `git commit`, no `git push`, no dependency
   installs unless the env is broken (then stop and report).
2. Work from the **repository root**. Conda env **`maf`**, Python 3.10+.
3. Azure CLI must be logged in to subscription **T332 - TCO**.
4. Use **`python -m maf.slice3`** only (not slice 1/2, not Prompt Flow).
5. Turn 1 input is the test ID (`TC-001` … `TC-036`). The CLI looks up the
   deducted prompt. **Never** type the test ID again on a later turn — that
   would re-send the whole prompt instead of answering the question.
6. Cap **6 turns** per case. If still incomplete, mark `stuck` and move on.
7. Continue after a single-case failure. Record the error; do not abort the
   remaining 35 unless Azure auth is broken for everyone.

## Preconditions (once)

```bash
az account show --query "{name:name, id:id}" -o json
# name must be T332 - TCO
conda activate maf
python -c "import agent_framework; print('ok')"
```

PowerShell: `conda activate maf` then the same `python` / `az` commands.

If `az account show` is the wrong subscription:

```bash
az account set --subscription "T332 - TCO"
```

If login is missing, run `az login` (device/browser as usual) and stop if you
cannot authenticate.

Record in `summary.json`: `git rev-parse HEAD`, `az account show` name, UTC
start time.

## Output layout

Create **one** run directory (UTC date-time):

```text
maf/runs/YYYYMMDD-HHMM-slice3/
  summary.json          # you maintain this as you go
  TC-001/
    history.json        # written by --history
    turn-01.json        # stdout of turn 1
    turn-01.stderr.txt
    turn-02.json        # only if a follow-up ran
    ...
  TC-002/
    ...
```

Do not put logs anywhere else. JSON **must** be stdout only; node traces go to
stderr (`MAF_LOG` unset is fine).

## How to tell “asked a question” vs “job pack”

Read the turn JSON:

| Field | Question turn | Pack turn |
|---|---|---|
| `complete` | `false` | `true` |
| `missing` | non-empty list | `[]` |
| `route.kind` | `"string"` | `"json"` |
| `answer` | one clarifying question | PSW / Shop / Site style job pack |

Stop the case when `complete` is `true`. That `answer` is the artifact to
compare later.

## Per-case loop

For `TC-001` through `TC-036`:

**Turn 1 (bash):**

```bash
ID=TC-001
DIR=maf/runs/YYYYMMDD-HHMM-slice3/$ID
mkdir -p "$DIR"
python -m maf.slice3 --history "$DIR/history.json" "$ID" \
  > "$DIR/turn-01.json" 2> "$DIR/turn-01.stderr.txt"
```

**Turn 1 (PowerShell):**

```powershell
$Id = "TC-001"
$Dir = "maf/runs/YYYYMMDD-HHMM-slice3\$Id"
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
python -m maf.slice3 --history "$Dir\history.json" $Id `
  1> "$Dir\turn-01.json" 2> "$Dir\turn-01.stderr.txt"
```

Then:

1. If the process **exits non-zero**, copy stderr into `summary.json` for that
   case (`error`), skip follow-ups, next ID.
2. If `complete` is **true**, done. `turns: 1`, `asked: false`.
3. If `complete` is **false**, compose a **short follow-up** (next section).
   Run turn 2 with **that text**, same `--history` file, **not** `TC-00N`:

```bash
python -m maf.slice3 --history "$DIR/history.json" "Tie-ins at TP-001 and TP-002." \
  > "$DIR/turn-02.json" 2> "$DIR/turn-02.stderr.txt"
```

Repeat until `complete` is true or turn 6.

Update `summary.json` after every case so a crash still leaves partial results.

## Follow-up answers

Use the **smallest** reply that fills what `missing` lists. Prefer the canned
line below for that test ID. If `missing` has several fields, you may send
**one** combined sentence covering all of them.

Do **not** invent process pressures/temperatures. If asked, say
`Process conditions remain TBD.`

### Default fillers (when the cheat sheet says “use defaults”)

| If asked about | Reply with |
|---|---|
| Tie-ins / TP / placeholders | `Tie-ins at TP-001 and TP-002.` |
| Diameter / NPS / inch | NPS from the line number in `maf/tracker_cases.json` (e.g. `24 inch`, `1/2 inch`) |
| Insulation | `Insulated.` unless the deducted prompt or line id has `NI` / `Uninsulated` → `Uninsulated.` |
| Heat tracing | Copy the deducted prompt (`no heat tracing` or `electric heat tracing`). |
| Scope / repair type | Map **cohort** from `maf/tracker_cases.json` (table below). |

Cohort → scope reply:

- `TLR single-removal` / `TLR multi-removal` → `TLR removal and replace the damaged pipe section.`
- `Flange replacement` → `Flange replacement.`
- `Pipe section repl.` / `Section + support` → `Replace the pipe section.`
- `Pipe extension` → `Pipe extension.`
- `Elbow replacement` → `Elbow replacement.`
- `Tee/branch repl.` → `Tee replacement.`

### First-turn expectation (local extract/merge, no Azure)

These 19 IDs should produce a **pack on turn 1**. If they **ask**, still
answer and continue, but set `unexpected_ask: true` in `summary.json`.

`TC-001`, `TC-003`, `TC-005`, `TC-006`, `TC-008`, `TC-009`, `TC-010`,
`TC-011`, `TC-012`, `TC-015`, `TC-016`, `TC-017`, `TC-018`, `TC-019`,
`TC-020`, `TC-021`, `TC-024`, `TC-025`, `TC-034`

These 17 IDs are **likely to ask** on turn 1. Use the canned reply. That is
expected with current merge/validate (empty tie-in list counts as missing).

| ID | Likely `missing` | Canned follow-up |
|---|---|---|
| TC-002 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-004 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-007 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-013 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-014 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-022 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-023 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-026 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-027 | scope_type | `Tee replacement.` |
| TC-028 | scope_type, placeholders_TP | `Flange replacement. Tie-ins at TP-001 and TP-002.` |
| TC-029 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-030 | placeholders_TP | `Tie-ins at TP-001 and TP-002.` |
| TC-031 | scope_type, insulation, dia_in, placeholders_TP | `Flange replacement. Insulated. Diameter 2 inch. Tie-ins at TP-001 and TP-002.` |
| TC-032 | scope_type, insulation, placeholders_TP | `Flange replacement. Insulated. Tie-ins at TP-001 and TP-002.` |
| TC-033 | scope_type | `Replace the pipe section.` |
| TC-035 | scope_type | `Replace the pipe section.` |
| TC-036 | insulation | `Insulated.` |

If `missing` does not match the table, still answer from **Default fillers**.
Log `followups` as the exact strings you sent.

## `summary.json` schema

Write this file at the start (empty `cases`) and append after each ID:

```json
{
  "run_id": "YYYYMMDD-HHMM-slice3",
  "started_utc": "",
  "finished_utc": "",
  "git_head": "",
  "azure_subscription": "T332 - TCO",
  "command": "python -m maf.slice3",
  "cases": [
    {
      "id": "TC-001",
      "turns": 1,
      "asked": false,
      "unexpected_ask": false,
      "complete_final": true,
      "stuck": false,
      "missing_first": [],
      "followups": [],
      "wps_result": null,
      "nde_result": null,
      "material": null,
      "answer_chars": 0,
      "error": null
    }
  ]
}
```

Copy `wps_result`, `nde_result`, `material` from the **last** turn JSON when
`complete` is true. `answer_chars` is `len(answer)` on that turn. `followups`
is the list of strings you typed on turns 2+.

Do not paste the full job pack into `summary.json` (it lives in `turn-NN.json`).

## Done when

- All 36 IDs have a folder, **or** every skipped ID has `error` in `summary.json`.
- `finished_utc` is set.
- You did not modify tracked source files (`git status` should only show
  `maf/runs/...` and possibly untracked run files).

Zip the run directory and leave it in `maf/runs/`. Tell the human the folder
name and how many cases ended `complete_final: true` vs `stuck` vs `error`.

## Do not

- Compare wording to the Excel Run Log (human will do that).
- Re-run a case to “improve” the pack.
- Open Azure Portal, deploy agents, or rotate keys.
- Use a Search API key; the client uses `az login`.
