from promptflow import tool

from src.pf_jobpack.search import acs_search as package_acs_search


@tool
def acs_search(endpoint: str, index_name: str, api_key: str, api_version: str, body: dict) -> dict:
    return package_acs_search(endpoint, index_name, api_key, api_version, body)