from promptflow import tool

from pf_jobpack.pwht import check_pwht_flag


@tool
def check_pwht_flag_tool(search_result, line_class: str):
    return check_pwht_flag(search_result, line_class)
