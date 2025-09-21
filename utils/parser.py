import io
from typing import Optional

def extract_text_from_txt(file_bytes: bytes, encoding: str = "utf-8") -> str:
    return file_bytes.decode(encoding, errors="ignore")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
    except Exception:
        raise RuntimeError("pdfplumber is required to parse PDFs")

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
    except Exception:
        raise RuntimeError("python-docx is required to parse DOCX files")

    f = io.BytesIO(file_bytes)
    doc = Document(f)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_text(file_bytes: bytes, filename: Optional[str] = None) -> str:
    """Detect by filename extension when provided; otherwise try TXT -> DOCX -> PDF."""
    if filename:
        lower = filename.lower()
        if lower.endswith(".txt"):
            return extract_text_from_txt(file_bytes)
        if lower.endswith(".pdf"):
            return extract_text_from_pdf(file_bytes)
        if lower.endswith(".docx"):
            return extract_text_from_docx(file_bytes)

    # Fallback attempts
    try:
        return extract_text_from_txt(file_bytes)
    except Exception:
        pass
    try:
        return extract_text_from_docx(file_bytes)
    except Exception:
        pass
    try:
        return extract_text_from_pdf(file_bytes)
    except Exception:
        pass
    raise RuntimeError("Unable to extract text from provided file")
