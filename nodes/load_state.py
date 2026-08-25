from promptflow import tool

from pf_jobpack.state import load_state


@tool
def load_state_tool(chat_history: list) -> dict:
    return load_state(chat_history)
