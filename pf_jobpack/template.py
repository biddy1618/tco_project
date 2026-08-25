"""Job-pack text assembly.

Faithful port of the original ``template.py`` node. Given the validated facts
plus the NDE / WPS / material lookups, assemble the job-pack scope text used as
the source content for the final formatting LLM.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Union


def build_job_pack(facts: str, nde_result: str, wps_result: str, material: str) -> Union[Dict[str, Any], str]:
    if isinstance(facts, str):
        try:
            facts = json.loads(facts)
        except (json.JSONDecodeError, ValueError):
            return facts  # Not JSON -> return the raw string as-is

    # Safety net: if after parsing it's still not a dict, return original.
    if not isinstance(facts, dict):
        return str(facts)

    # If the WPS branch produced a long free-text message, surface it directly.
    if isinstance(wps_result, str) and len(wps_result.split()) > 6:
        return wps_result

    output_lines = []
    lines = []
    mvp = False

    # ---- HEADER ----
    output_lines.append("\nPRESENT SITUATION:")

    # ---- HEADER ----
    output_lines.append("\nPROPOSED SOLUTION:")

    # ---- HEADER ----
    output_lines.append("\nSCOPE OF WORK")

    # ---- Always include ----
    output_lines.append(
        "\nBUSINESS PARTNER (BP) shall strictly follow all relevant TCO Safety Instructions."
    )
    output_lines.append(
        "\nBUSINESS PARTNER (BP) shall follow all Quality Management (QM) requirements designated in the Quality Control package."
    )

    # ---- PRELIMINARY SITE WORK ----
    output_lines.append("\nPRELIMINARY SITE WORK (PSW):")

    tp_list = []
    if facts['has_tie_ins']:
        tp_list = facts.get("placeholders_TP", []) or []

        if tp_list:
            if len(tp_list) == 1:
                output_lines.append(f"\nPrior to start of mechanical activities, perform wall thickness testing at {tp_list[0]} to confirm that wall thickness is adequate for welding. Results shall be reviewed and approved by Fixed Equipment Reliability (FER) Unit Inspector.")
            elif len(tp_list) == 2:
                output_lines.append(f"\nPrior to start of mechanical activities, perform wall thickness testing at {tp_list[0]} and {tp_list[1]} to confirm that wall thickness is adequate for welding. Results shall be reviewed and approved by Fixed Equipment Reliability (FER) Unit Inspector.")
            elif len(tp_list) > 2:
                output_lines.append(f"\nPrior to start of mechanical activities, perform wall thickness testing at {', '.join([i for i in tp_list])} to confirm that wall thickness is adequate for welding. Results shall be reviewed and approved by Fixed Equipment Reliability (FER) Unit Inspector.")
            lines.append('15')
            output_lines.append("NOTE: Perform the wall thickness test by marking out and recording a matrix as directed by the TCO FER Unit Inspector.")

    # ---- Line 17 ----
    output_lines.append(
        "\nPrior to commencing any fabrication works verify dimensions, pipe routing and field weld locations on site."
    )

    if facts["scope_type"] == 'machinery nozzle':
        output_lines.append("\nNOTE: When allocating FW & FFW locations for machinery nozzle connections, consider the possibility of final piping adjustment after nozzle alignment completion.")
        lines.append('18a')
    if facts["scope_type"] == 'fixed equipment nozzle or vessel nozzle':
        output_lines.append("\nNOTE: When allocating FW & FFW locations for fixed equipment nozzle connections, consider the possibility of final piping adjustment after nozzle alignment completion.")
        lines.append('18b')
    if facts["scope_type"] == 'PSV connection':
        output_lines.append("\nNOTE: When allocating FW & FFW locations for PSV inlet/outlet connections, consider the possibility of final piping adjustment after nozzle alignment completion.")
        lines.append('18b')

        output_lines.append("\nNOTE: Invite Responsible Engineer to verify dimensions / internal configuration / XXX on site, once vessel is isolated.")

    # ---- Line 22 (only if new piping route) ----
    if facts["new_piping_route"]:
        output_lines.append(
            "\nPrior to excavation works, perform surveying for underground utilities in coordination with TCO Lead Field Surveyor."
        )
        # ---- Line 23 ----
        output_lines.append(
            "\nPerform excavation and install concrete foundation as per isometric drawing 00-YYYY-L-ZZZZ."
        )

    if facts["replace_existing_equipment_diff_weight"] and (facts['scope_type'] == 'vessel replacement' or facts['scope_type'] == 'Valve replacement'):
        output_lines.append("\nConsider the weight of the new equipment indicated on drawing XXXX during developing execution steps and lifting plan.")
        output_lines.append("\nNOTE: DTEC completed required engineering studies of existing/new piping, foundation & supports and confirmed new equipment weight is within allowable loads.")

    if facts['scope_type'] != 'Valve replacement':
        output_lines.append("\nSHOP WORK:")

        output_lines.append('\nWithdraw materials required for this Job Pack from TCO Warehouse according to Material Request(s).')

        if nde_result == "Yes":
            output_lines.append('\nPerform Positive Material Identification (PMI) as per TCO RE QM SWP-20 Procedure on all corrosion resistant alloy (CRA) materials and weld consumables.')

        if facts['spool_prefab'] or ('TLR' in facts['scope_type']) or ('Flange replacement' in facts['scope_type']):
            output_lines.append('\nPrefabricate pipe spools as per isometric drawing(s) 00-YYYY-L-ZZZZ. Use TCO-approved Welding Procedure Specification(s) (WPSs) indicated on isometric drawing(s). BP shall comply with TCO Guideline 16-0015-MI for socket-welded joints.')
            lines.append('29a')
        # MVP
        if facts['spool_prefab'] and mvp == True:
            output_lines.append('\nPrefabricate pipe spools and pipe supports, as per isometric drawing(s) 00-YYYY-L-ZZZZ. Use TCO-approved Welding Procedure Specification(s) (WPSs) indicated on isometric drawing(s). BP shall comply with TCO Guideline 16-0015-MI for socket-welded joints.')
            lines.append('29b')

        if wps_result == "Yes":
            output_lines.append('\nPerform PWHT as specified by WPS and per TES PIM-SU-2505.')
            lines.append('30a')
        if wps_result == "Yes" and facts['scope_type'] == 'pipeline':
            output_lines.append('\nPerform PWHT as specified by WPS and per TES W-ST-2011.')
            lines.append('30b')
        if wps_result == "Yes" and facts['scope_type'] == 'gas injection':
            output_lines.append('\nPerform PWHT as specified by WPS and per TES W-ST-2016.')
            lines.append('30c')
        if wps_result == "Yes" and facts['scope_type'] == 'wellhead':
            output_lines.append('\nPerform PWHT as specified by WPS and per TES W-ST-2026.')
            lines.append('30d')
        if wps_result == "Yes" and facts['scope_type'] == 'heavy wall piping':
            output_lines.append('\nPerform PWHT as specified by WPS and per TES W-ST-2028.')
            lines.append('30e')

        if facts['spool_prefab'] and ('29a' in lines or '29b' in lines) and ('30a' not in lines):
            output_lines.append('\nPerform non-destructive examination (NDE) as specified on drawing 00-YYYY-L-ZZZZ.')
            lines.append('31a')
        if '31a' not in lines:
            # for TLR
            if 'TLR' in facts['scope_type'] and ('29a' in lines or '29b' in lines) and ('30a' not in lines):
                output_lines.append('\nPerform non-destructive examination (NDE) as specified on drawing 00-YYYY-L-ZZZZ.')
            # for Flange
            if 'Flange replacement' in facts['scope_type'] and ('29a' in lines or '29b' in lines) and ('30a' not in lines):
                output_lines.append('\nPerform non-destructive examination (NDE) as specified on drawing 00-YYYY-L-ZZZZ.')

        if facts['spool_prefab'] and ('29a' in lines or '29b' in lines) and ('30a' in lines):
            output_lines.append('\nPerform non-destructive examination (NDE) and hardness testing of shop welds, as specified on drawing 00-YYYY-L-ZZZZ.')
            lines.append('31b')

        if '31b' in lines:
            output_lines.append('\nNOTE: Perform NDE and hardness testing only after PWHT!')

        if ('29a' in lines) or ('29b' in lines):
            output_lines.append('\nNOTE: BP must check with MaxTrax admin on NDE requirements prior to commence welding works.')

        if (facts['spool_prefab'] or ('29a' in lines or '29b' in lines)) and ('TLR' not in facts['scope_type']) and ('Flange replacement' not in facts['scope_type']):
            output_lines.append('\nPerform shop hydrostatic testing of flanged spools as specified on isometric drawing(s) 00-YYYY-L-ZZZZ in accordance with TES PIM-SU-3541-TCO.')
            lines.append('34a')

        if ('29a' in lines or '29b' in lines) and '30b' in lines:
            output_lines.append("\nPerform shop hydrostatic testing of ASME B31.4 / B31.8 pipeline components in accordance with TCO Procedure X-000-L-PRO-0001 as per isometric drawing(s) 00-YYYY-L-ZZZZ – 4-hour duration.")

        if material == 'SS' and '34a' in lines:
            output_lines.append('\nNOTE: Test water used for 300-series stainless steel piping shall be water with chloride content of less than 50 ppm. Perform Water Sampling and Analysis per TES PIM-SU-3541-TCO Section 5.')

        if material == "CS":
            output_lines.append('\nAbrasive blast and coat new piping spools and supports, as specified on isometric drawing 00-YYYY-L-ZZZZ in accordance with TES COM-SU-5191-TCO.')
            output_lines.append('\nNOTE: Mask-off field-weld joints and flange faces prior to coating.')

    output_lines.append("\nSITE WORK:")
    output_lines.append("\nPerform relevant job safety assessments (PPHA & JSA) and obtain required Permits-to-Work (PTWs).")
    output_lines.append("\nDemarcate work area as necessary and erect scaffolding for access.")
    output_lines.append("\nNOTE: TCO Operations shall isolate, depressurize, drain and ready for Hot Work, Equipment and Piping associated with this Project, if and as applicable, and shall hand it over to BUSINESS PARTNER (BP); fully accessible, safe and Locked-Out-Tagged-Out (LOTO) as scheduled and agreed between TCO Operations and BP.")

    if facts['existing_spring_support_reuse'] == False:
        output_lines.append('\nA spring stopping pin must be installed before pipe dismantling. Note that the pin must be removed on the same condition as it was installed. If pipe was full at installation of pin, new pipe must be filled prior to pin removal. Spring level / indicator must be marked on hot and cold conditions.')

    if facts['insulation'] == True:
        output_lines.append('\nRemove all cladding and insulation to the extent required.')
        lines.append('42')

    if facts["scope_type"] == 'machinery nozzle':
        output_lines.append('\n.Invite Machinery Maintenance team to install dial gauges prior to existing piping dismantle to record “Zero” position of the compressor/pump.')
        lines.append('44a')
    if '44a' in lines:
        output_lines.append('\nNOTE: Gauges stay on until all work complete. Last step is record of gauges and removal.')

    if facts['heat_tracing']:
        if 'electric' in facts['heat_tracing']:
            output_lines.append(f"\nArrange with Tengiz Turnaround Team (TTT) I&E Coordinator [OR]  Zone Maintenance to isolate, LOTO and remove electric trace heating and instruments from associated piping per I&E Job Pack {facts['ie_doc_no']}.")
            lines.append('45a')
        if 'water' in facts['heat_tracing'] or 'steam' in facts['heat_tracing'] or 'contro-trace' in facts['heat_tracing']:
            output_lines.append('\nCarefully remove for reinstatement (or Demolish) hot water / steam tracing where necessary.')
            lines.append('45b')

    if '45a' in lines:
        output_lines.append('\nNOTE: BP to match mark, call a unit operator, show the mark and record location prior to cutting and removal to aid in reinstatement of heat tracing.')

    if '15' in lines:
        if len(tp_list) == 1:
            output_lines.append(f"\nApply and sign special tape, which determines the place of cutting the pipe, according to SP-26 at {tp_list[0]}. Follow all the steps of SP-26.")
        elif len(tp_list) == 2:
            output_lines.append(f"\nApply and sign special tape, which determines the place of cutting the pipe, according to SP-26 at {tp_list[0]} and {tp_list[1]}. Follow all the steps of SP-26.")
        elif len(tp_list) > 2:
            output_lines.append(f"\nApply and sign special tape, which determines the place of cutting the pipe, according to SP-26 at {', '.join([i for i in tp_list])}. Follow all the steps of SP-26.")
        lines.append('46')

    if '46' in lines:
        output_lines.append("\nCold Cut, unbolt and remove existing piping and pipe supports per 'Destruct Detail' of isometric drawing 00-YYYY-L-ZZZZ.")
        output_lines.append('\nMake good any remaining foundations and/or metal structures and perform coating repairs per TES COM-SU-5191-TCO.')
        lines.append('47a')

    if facts['new_piping_route']:
        output_lines.append('\nRemove the redundant plinths and/or metal structures, supports.')

    if facts['hydrogen_bake_out']:
        output_lines.append('\n.Perform hydrogen bake-out in the weld zone of each tie-in points as shown on isometric drawing(s) 00-YYYY-L-ZZZZ following requirements in TES PIM-SU-2505.')

    if '47a' in lines:
        if len(tp_list) == 1:
            output_lines.append(f"\nBevel cut ends of existing piping at the tie-in point {tp_list[0]} for field welding as shown on isometric drawing(s) 00-YYYY-L-ZZZZ")
        elif len(tp_list) == 2:
            output_lines.append(f"\nBevel cut ends of existing piping at the tie-in points {tp_list[0]} and {tp_list[1]} for field welding as shown on isometric drawing(s) 00-YYYY-L-ZZZZ")
        elif len(tp_list) > 2:
            output_lines.append(f"\nBevel cut ends of existing piping at the tie-in points {', '.join([i for i in tp_list])} for field welding as shown on isometric drawing(s) 00-YYYY-L-ZZZZ")
        lines.append("49")

    if '49' in lines:
        output_lines.append("\nInspect the prepared weld bevel ends 100% VT and 100 % MT/PT for defects.")
        output_lines.append("\nNOTE: Perform inspection of weld bevels and nipo-flange landings PRIOR to welding.")

    if nde_result == "Yes":
        output_lines.append("\nPerform PMI at field joints per TCO RE QM SWP-20 on alloy materials listed in SWP-20 Appendix 20-1.")
        lines.append("51")

    if '47a' in lines:
        output_lines.append("\nInstall piping as specified on isometric drawing 00-YYYY-L-ZZZZ. For field welds use TCO-approved WPSs indicated on isometric drawing(s).")
        lines.append('52a')

    if facts["scope_type"] == 'machinery nozzle':
        output_lines.append('\nNOTE: Verify the piping alignment with respect to machinery suction/discharge nozzle before the field welding. Flange alignment shall be parallel to pump nozzle with ability to insert/remove bolting without any binding. Flange-face gaps shall only accommodate Gasket including Spec Blind as applicable. API 686 shall be followed for alignment requirements')

    if wps_result == "Yes":
        output_lines.append("\nPerform PWHT of field joints as specified by WPS and in compliance with TES PIM-SU-2505.")

    if '52a' in lines and wps_result == 'No':
        output_lines.append("\nPerform NDE of field welds, as specified on isometric drawing(s) 00-YYYY-L-ZZZZ.")
        lines.append('57a')
    if '52a' in lines and wps_result == 'Yes':
        output_lines.append("\nPerform NDE and hardness testing of field welds, as specified on isometric drawing(s) 00-YYYY-L-ZZZZ.")
        lines.append('57b')

    if '57b' in lines:
        output_lines.append("\nNOTE: Perform NDE and Hardness Testing only after PWHT!")
    if '57a' in lines or '57b' in lines:
        output_lines.append("\nNOTE: BP must check with MaxTrax admin on NDE requirements prior to commence welding works.")

    if '52a' in lines:
        output_lines.append("\nPerform field hydrostatic testing of new piping as specified on isometric drawing(s) 00-YYYY-L-ZZZZ in accordance with TES PIM-SU-3541-TCO")
        lines.append('58a')

    if '52a' in lines and facts['scope_type'] == 'pipeline':
        output_lines.append("\nPerform shop hydrostatic testing of ASME B31.4 / B31.8 pipeline components in accordance with TCO Procedure X-000-L-PRO-0001 as per isometric drawing(s) 00-YYYY-L-ZZZZ – 4-hour duration.")

    if '58a' in lines and material == "SS":
        output_lines.append("\nNOTE: Test water used for 300-series stainless steel piping shall be water with chloride content less than 50 ppm.  Perform Water Sampling and Analysis per TES PIM-SU-3541-TCO Section 5.")
    if material == 'CS':
        output_lines.append("\nPerform surface preparation and touch up field welds and any other coating damages in accordance with TES COM-SU-4743-TCO and coating system(s) per TES COM-SU-5191-TCO specified on drawings.")

    if '45a' in lines and '51' in lines:
        output_lines.append("\nApply Aerogel (Pyrogel) insulation on seam welds prior heat tracing installation in accordance with P-ST-6199.")

    if '45a' in lines:
        output_lines.append(f"\nArrange with TTT I&E Coordinator [OR]  Zone Maintenance to reinstate / install related electric trace heating and instruments, as per I&E Job Pack {facts['ie_doc_no']}.")
    if '45b' in lines:
        output_lines.append("\nReinstate hot water / steam tracing and conduct NDE as well as service testing of each separate loop.")

    output_lines.append("\nAll QM piping passport documentation (A-category Checklists) to be verified and signed by TCO-approved QM Inspector prior to PSSR, but not later than 24 hours after mechanical scope completion.")
    lines.append('62')

    output_lines.append("\nAdvise xxxxx yyyyy/ zzzzz mmmm, DTEC KTL Plant Support / DTEC T/A / SGP/SGI, / FUPO Engineer at ext. 0000 about work completion and invite all necessary people to PSSR.")

    if '44a' in lines:
        output_lines.append("\nNOTE: Arrange with RE Integrated Machinery Inspection (IMI) group (x3969/x7375) for inspection of suction/discharge flange alignment prior to torqueing of bolts to rotating equipment nozzles.")
    if '18a' in lines:
        output_lines.append("\nNOTE: Arrange with RE Integrated Machinery Inspection (IMI) group (x3969/x7375) for inspection of suction/discharge flange alignment prior to torqueing of bolts to rotating equipment nozzles.")
    if '18b' in lines:
        output_lines.append("\nNOTE: Fixed Equipment nozzle flange alignment to be witnessed and accepted stress-free by TCO Designs & Technical Engineering Center (DTEC) and RE QM Bolting Team prior to PSSR.")
    if '18c' in lines:
        output_lines.append("\nNOTE: PSV connections flange alignment to be witnessed and accepted stress-free by TCO Designs & Technical Engineering Center (DTEC) and RE QM Bolting Team prior to PSSR.")

    if facts['scope_type'] == 'swing elbow':
        output_lines.append('\nNOTE: Swing Elbow connection flange alignment to be witnessed and accepted stress-free by TCO Designs & Technical Engineering Center (DTEC) and RE QM Bolting Team prior to PSSR.')

    if '62' in lines:
        output_lines.append("\nJob Pack Coordinator shall submit the completed PIC check-list to Operations department after being signed by Quality Management group. (Form is provided by QM Dept.).")
        lines.append('64')
    if '64' in lines:
        output_lines.append("\nConduct PSSR and close out A-category punch points.")

    if '42' in lines:
        output_lines.append("\nFollowing PSSR reinstate / install insulation and cladding, as per TES IRM-SU-1381-TCO and as specified on isometric drawing 00-YYYY-L-ZZZZ.")
        lines.append('66')

    if '66' in lines:
        output_lines.append("\nClose out all B-category punch points and remove associated scaffolding.")
    output_lines.append("\nClean up the work area and demobilize from site.")

    output_lines.append("\nAFTER COMPLETION OF WORK:")
    output_lines.append("\nFinal as-built package (including B-category Checklist) submitted to TCO QM group within 2 weeks.")
    output_lines.append("\nReturn excess material to TCO Warehouse.")

    final_text = "\n".join(output_lines)

    return {"final_text": final_text}
