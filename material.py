from promptflow import tool

from src.pf_jobpack.material import check_material_ss as package_check_material_ss


@tool
def check_material_ss(search_output):
    return package_check_material_ss(search_output)