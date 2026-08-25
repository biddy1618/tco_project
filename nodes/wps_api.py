from promptflow import tool

from pf_jobpack.search import acs_search


@tool
def acs_search_tool(endpoint: str, index_name: str, api_key: str, api_version: str, body):
    return acs_search(endpoint, index_name, api_key, api_version, body)
