from promptflow import tool

from pf_jobpack.state import route_prev


@tool
def route_prev_tool(prev) -> dict:
    return route_prev(prev)
