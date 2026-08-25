from promptflow import tool

from pf_jobpack.extraction import build_scope_json_from_input


@tool
def my_python_tool(user_input: str) -> dict:
    return build_scope_json_from_input(user_input)
