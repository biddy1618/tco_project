from promptflow import tool

from src.pf_jobpack.lookup import check_nde_search as package_check_nde_search


@tool
def my_python_tool(input1: list, line_class: str) -> str:
    return package_check_nde_search(input1, line_class)