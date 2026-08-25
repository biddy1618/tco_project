from promptflow import tool

from pf_jobpack.search import build_wps_query


@tool
def my_python_tool(as_string: str = "", as_dict: dict = None):
    return build_wps_query(as_string=as_string, as_dict=as_dict)
