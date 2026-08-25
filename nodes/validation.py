from promptflow import tool

from pf_jobpack.state import validate_state


@tool
def my_python_tool(updated_json) -> dict:
    return validate_state(updated_json)
