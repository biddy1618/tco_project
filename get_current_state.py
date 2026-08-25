from promptflow import tool

from src.pf_jobpack.conversation import get_current_state as package_get_current_state


@tool
def get_current_state(chat_history) -> dict:
    return package_get_current_state(chat_history)