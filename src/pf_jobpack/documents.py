"""Document generation helpers."""

from __future__ import annotations

import json

from docx import Document


def create_word_doc(text) -> str:
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                text = parsed
        except Exception:
            pass

    if isinstance(text, dict):
        text = text.get("final_text", "")

    if not isinstance(text, str):
        text = str(text)

    doc = Document()

    for line in text.split("\n"):
        doc.add_paragraph(line)

    file_path = "job_pack.docx"
    doc.save(file_path)

    return file_path