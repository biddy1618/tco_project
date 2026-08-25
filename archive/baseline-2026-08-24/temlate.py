from typing import Dict, Any, List
from promptflow import tool

@tool
def build_job_pack(facts: Dict[str, Any]) -> Dict[str, Any]:

    output_lines = []

    # ---- HEADER ----
    output_lines.append("PRESENT SITUATION:")

    # ---- Line 8 ----
    output_lines.append(facts["problem_statement"])

    # ---- HEADER ----
    output_lines.append("\nPROPOSED SOLUTION:")

    # ---- Line 10 ----
    output_lines.append(facts["proposed_solution"])

    # ---- HEADER ----
    output_lines.append("\nSCOPE OF WORK")

    # ---- Always include ----
    output_lines.append(
        "BUSINESS PARTNER (BP) shall strictly follow all relevant TCO Safety Instructions."
    )
    output_lines.append(
        "BUSINESS PARTNER (BP) shall follow all Quality Management (QM) requirements designated in the Quality Control package."
    )

    # ---- PRELIMINARY SITE WORK ----
    output_lines.append("\nPRELIMINARY SITE WORK (PSW):")

    # ---- Line 15 ----
    if facts["has_tie_ins"]:
        tp1, tp2 = facts["placeholders_TP"]
        output_lines.append(
            f"Prior to start of mechanical activities, perform wall thickness testing at {tp1} and {tp2}."
        )

        # ---- Line 16 (paired) ----
        output_lines.append(
            "NOTE: Perform the wall thickness test by marking out and recording a matrix as directed by the TCO FER Unit Inspector."
        )

    # ---- Line 17 ----
    if facts["fabrication_in_scope"]:
        output_lines.append(
            "Prior to commencing any fabrication works verify dimensions, pipe routing and field weld locations on site."
        )

    if facts["pump_compressor_vessel_psv_in_scope"]:
        output_lines.append("NOTE: When allocating FW & FFW locations for machinery [OR] vessel nozzle [OR] PSV — strain considerations apply.")
        
        output_lines.append(
            "NOTE: Invite Responsible Engineer to verify dimensions / internal configuration / XXX on site, once vessel is isolated."
        )

    # ---- Line 22 (only if new piping route) ----
    if facts["new_piping_route"]:
        output_lines.append(
            "Prior to excavation works, perform surveying for underground utilities in coordination with TCO Lead Field Surveyor."
        )

        # ---- Line 23 ----
        output_lines.append(
            "Perform excavation and install concrete foundation as per isometric drawing 00-YYYY-L-ZZZZ."
        )

        output_lines.append(
            "Consider the weight of the new equipment indicated on drawing XXXX during developing execution steps and lifting plan."
        )

        output_lines.append(
            "NOTE: DTEC completed required engineering studies of existing/new piping, foundation & supports and confirmed new equipment weight is within allowable loads."
        )

    final_text = "\n".join(output_lines)

    return {
        "final_text": final_text
    }