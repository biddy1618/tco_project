from promptflow import tool

from pf_jobpack.template import build_job_pack


@tool
def build_job_pack_tool(facts: str, nde_result: str, wps_result: str, material: str):
    return build_job_pack(facts, nde_result, wps_result, material)
