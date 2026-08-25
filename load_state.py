from promptflow.core import tool

from src.pf_jobpack.state import load_state as package_load_state


@tool
def load_state(chat_history: list) -> dict:
    return package_load_state(chat_history)