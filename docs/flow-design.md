# Flow Design

## Purpose

Convert a repair request into a job-pack style output using Prompt Flow as the current runtime.

## High-Level Shape

1. Normalize the user input.
2. Extract line class, scope type, tie-ins, insulation, heat tracing, and related flags.
3. Merge the new extraction with prior conversation state.
4. Validate whether enough fields are present.
5. Ask for missing information or continue.
6. Look up WPS/PWHT, NDE, and material information from Azure AI Search.
7. Assemble the final job-pack text.

## Main Inputs

- `question`
- `chat_history`

## Main Outputs

- `answer`
- `merge_state`

## Runtime Pieces

- Prompt Flow DAG: orchestration layer.
- Python helpers: extraction, state, lookup, PWHT/material, document generation.
- Prompt templates: spell-check, ask/finalize, final text shaping.

## Validation Strategy

- Keep the local harness runner green after each refactor slice.
- Use a minimal Prompt Flow smoke test only after the structure is stable.
- Migrate to MAF after the Prompt Flow shape is confirmed.