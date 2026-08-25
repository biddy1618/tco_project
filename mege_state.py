from promptflow.core import tool

from src.pf_jobpack.state import merge_state as package_merge_state


@tool
def merge_state(prev_state: dict, new_extraction: dict) -> dict:
    return package_merge_state(prev_state, new_extraction)