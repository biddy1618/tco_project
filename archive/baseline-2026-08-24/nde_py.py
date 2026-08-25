from promptflow import tool


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def my_python_tool(input1: list, line_class: str) -> str:
    
    if line_class not in input1[0].get("text"):
        return None
    
    else:

        if input1 and input1[0].get("metadata") == 100:
            return "Yes"
        return "No"
