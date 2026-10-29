from dataclasses import dataclass
import hashlib
import pymupdf as fitz

@dataclass
class Passage:
    text: str
    source: str
    page: int
    chunk_id: str

def extract_pdf(data: bytes, filename: str, chunk_size: int = 600, overlap: int = 100) -> list[Passage]:
    if not data:
        raise ValueError("PDF is empty")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Could not read PDF: {exc}") from exc
    if doc.needs_pass:
        raise ValueError("Password-protected PDFs are not supported")
    if doc.page_count == 0:
        raise ValueError("PDF contains no pages")
    passages = []
    for page_index, page in enumerate(doc, start=1):
        text = " ".join(page.get_text("text").split())
        offset = 0
        while offset < len(text):
            start = offset
            if start and text[start - 1] != " ":
                boundary = text.rfind(" ", max(0, start - 40), start)
                if boundary >= 0:
                    start = boundary + 1
            end = min(start + chunk_size, len(text))
            if end < len(text) and text[end] != " ":
                boundary = text.rfind(" ", max(start + 1, end - 40), end)
                if boundary > start:
                    end = boundary
            chunk = text[start:end].strip()
            if chunk:
                key = hashlib.sha256(f"{filename}:{page_index}:{start}:{chunk}".encode()).hexdigest()[:16]
                passages.append(Passage(chunk, filename, page_index, key))
            if end >= len(text):
                break
            next_offset = max(start + 1, end - overlap)
            if next_offset and text[next_offset - 1] != " ":
                boundary = text.find(" ", next_offset, min(len(text), next_offset + 40))
                if boundary >= 0:
                    next_offset = boundary + 1
            offset = next_offset
    if not passages:
        raise ValueError("PDF has no extractable text")
    return passages
