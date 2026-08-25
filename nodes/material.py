from promptflow import tool

from pf_jobpack.material import check_material_ss


@tool
def check_material_ss_tool(search_output) -> str:
    return check_material_ss(search_output)
