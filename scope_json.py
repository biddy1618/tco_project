from promptflow import tool

from src.pf_jobpack.scope import build_scope_json_from_input as package_build_scope_json_from_input


@tool
def build_scope_json_from_input(user_input: str) -> dict:
    return package_build_scope_json_from_input(user_input)