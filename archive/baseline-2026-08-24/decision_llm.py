from promptflow import tool


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def my_python_tool(line_class: str, scope_type: str, template_llm: str) -> str:

    def to_text(x):
        if x is None:
            return ""
        if isinstance(x, str):
            return x
        return str(x)

    if line_class == 'outdated_or_missing':
        return 'Line class matches, but PWHT information is missing or outdated. Please provide an another line class.'
    elif line_class == 'mismatch':
        return 'Validation failed: The extracted line class does not match the expected value.'
    elif line_class == 'cannot_determine':
        return 'Unable to determine the line class from the input text. Please check the data or provide more details.'
    
    if line_class == 'pass':

        if scope_type == 'mismatch':
            return 'Validation failed: The extracted scope type does not match the expected value. Please check the data or provide more details.'
        if scope_type == 'cannot_determine': 
            return 'Unable to determine the scope type from the input text. Please check the data or provide more details.'

        if scope_type == 'pass':
            
            # template = to_text(template_llm)

            # md = []
            # md.append(template)
            return template_llm