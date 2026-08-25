from promptflow import tool

from src.pf_jobpack.pwht import check_pwht_flag as package_check_pwht_flag


@tool
def check_pwht_flag(search_result, line_class):
    return package_check_pwht_flag(search_result, line_class)