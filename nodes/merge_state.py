from promptflow import tool

from pf_jobpack.state import merge_state


@tool
def merge_state_tool(prev_state: dict, new_extraction: dict) -> dict:
    return merge_state(prev_state, new_extraction)
