from promptflow import tool

@tool
def merge_outputs(left_result, right_result) -> str:
    """
    Combines two scenario outputs into one markdown message for a single chat response.
    left_result/right_result can be dict/list/str depending on upstream nodes.
    """

    def to_text(x):
        if x is None:
            return ""
        if isinstance(x, str):
            return x
        return str(x)

    # Example formatting sections
    left_text = to_text(left_result)
    right_text = to_text(right_result)

    md = []
    md.append("## Scenario A (Class extraction / lookup)")
    md.append(left_text if left_text else "No output from Scenario A.")
    md.append("")
    md.append("## Scenario B (Filtered material list by size)")
    md.append(right_text if right_text else "No output from Scenario B.")

    return "\n".join(md)
