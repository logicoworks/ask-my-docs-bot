from io import BytesIO

import pdfplumber


def extract_pages(pdf_bytes: bytes) -> list[str]:
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]
