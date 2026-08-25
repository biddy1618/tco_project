from promptflow import tool
from docx import Document
import json

@tool
def create_word_doc(text) -> str:
    # If text comes as JSON string, parse it
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                text = parsed
        except Exception:
            pass

    # If text is a dict, extract final_text
    if isinstance(text, dict):
        text = text.get("final_text", "")

    # Safety check
    if not isinstance(text, str):
        text = str(text)

    doc = Document()

    for line in text.split("\n"):
        doc.add_paragraph(line)

    file_path = "job_pack.docx"
    doc.save(file_path)

    return file_path