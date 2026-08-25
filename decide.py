from promptflow.core import tool

from src.pf_jobpack.conversation import decide as package_decide


@tool
def decide(state: dict) -> dict:
    return package_decide(state)