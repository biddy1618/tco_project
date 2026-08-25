from promptflow import tool

from src.pf_jobpack.lookup import build_wps_query as package_build_wps_query


@tool
def my_python_tool(as_string: str = "", as_dict=None):
    return package_build_wps_query(as_string=as_string, as_dict=as_dict)