from promptflow import tool

from src.pf_jobpack.conversation import merge_outputs as package_merge_outputs


@tool
def merge_outputs(left_result, right_result) -> str:
    return package_merge_outputs(left_result, right_result)