from promptflow import tool

from src.pf_jobpack.documents import create_word_doc as package_create_word_doc


@tool
def create_word_doc(text) -> str:
    return package_create_word_doc(text)