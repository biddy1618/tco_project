from promptflow.core import tool

# Fields the user can legitimately correct in a later turn (non-bool).
CORRECTABLE_FIELDS = {"line_class", "scope_type", 'ie_doc_no', 'dia_in', 'heat_tracing'}


def _is_empty(v) -> bool:
    """True if the value carries no information (should NOT overwrite anything)."""
    return v is None or v == "" or v == [] or v == {}


@tool
def merge_state(prev_state: dict, new_extraction: dict) -> dict:
    """
    Merge rules:
      1. Empty new values (None/""/[]/{}) never overwrite anything.
      2. Lists are unioned (order-preserving, dedup).
      3. Booleans are MONOTONIC: once True, stays True. False can be promoted to True,
         but True is never downgraded to False.
      4. Sticky: otherwise, keep prev unless the field is in CORRECTABLE_FIELDS.
    """
    merged = dict(prev_state or {})

    for k, v in (new_extraction or {}).items():
        # Rule 1: skip empty/uninformative new values
        if _is_empty(v):
            continue

        prev = merged.get(k)

        # Rule 2: list union
        if isinstance(v, list) and isinstance(prev, list):
            merged[k] = list(dict.fromkeys([*prev, *v]))
            continue

        # Rule 3: monotonic bool — True wins, False never overwrites True
        if isinstance(v, bool):
            if isinstance(prev, bool):
                merged[k] = prev or v          # False + True -> True; True + False -> True
            else:
                merged[k] = v                  # prev was None/empty -> take new
            continue

        # Rule 4: sticky — don't overwrite an already-set value unless correctable
        if not _is_empty(prev) and k not in CORRECTABLE_FIELDS:
            continue

        merged[k] = v

    return merged