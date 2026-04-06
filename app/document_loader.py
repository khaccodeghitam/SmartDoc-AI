from pathlib import Path
from typing import List

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.documents import Document


def load_pdf(path: str | Path) -> List[Document]:
    loader = PDFPlumberLoader(str(path))
    return loader.load()
