import io
import os
import httpx
import pdfplumber
from PyPDF2 import PdfReader


async def download_and_extract_resume(url: str, upload_dir: str) -> str:
    """Download a resume from URL and extract text."""
    if not url or str(url).lower() == "nan":
        return ""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content = resp.content
    except Exception:
        return ""

    return extract_text_from_pdf_bytes(content)


def extract_text_from_pdf_bytes(content: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber, fallback to PyPDF2."""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            return text.strip()
    except Exception:
        pass
    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception:
        return ""


def extract_text_from_pdf_file(path: str) -> str:
    """Extract text from a local PDF file."""
    with open(path, "rb") as f:
        return extract_text_from_pdf_bytes(f.read())
