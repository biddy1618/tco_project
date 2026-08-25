from promptflow import tool


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need

@tool
# def check_pwht_flag(search_result: dict) -> str:
#     pwht = search_result["value"][0]["pwht"]
#     return "Yes" if pwht.strip()[0].upper() == "Y" else "No"

def check_pwht_flag(search_result: dict, line_class: str) -> str:
    # 1. if no line class → do not evaluate
    if not line_class:
        return None   # or "" if you prefer

    # 2. validate search_result structure
    if not search_result or "value" not in search_result or not search_result["value"]:
        return None
    
    row = search_result["value"][0]
    if line_class.upper() not in row.get("line_class", "").upper():
        return None

    # 3. ensure pwht exists
    pwht = row.get("pwht")
    if not pwht or not isinstance(pwht, str):
        return None

    pwht_clean = pwht.strip().upper()
    if not pwht_clean:
        return None

    # 4. evaluate
    return "Yes" if pwht_clean.startswith("Y") else "No"