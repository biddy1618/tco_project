from promptflow import tool

from pf_jobpack.nde import check_nde_search


@tool
def my_python_tool(input1: list, line_class: str) -> str:
    return check_nde_search(input1, line_class)
