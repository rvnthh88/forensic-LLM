import pymupdf as fitz
import pytest

from core.processor import extract_pdf

def pdf_bytes(pages):
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    result = doc.tobytes()
    doc.close()
    return result

def test_extract_preserves_page_numbers_and_chunks():
    content = pdf_bytes(["authentication event " * 60, "process creation evidence"])
    passages = extract_pdf(content, "notes.pdf", chunk_size=120, overlap=20)
    assert passages
    assert {p.page for p in passages} == {1, 2}
    assert all(p.source == "notes.pdf" for p in passages)
    assert len({p.chunk_id for p in passages}) == len(passages)

def test_empty_corrupt_and_textless_pdfs_are_rejected():
    with pytest.raises(ValueError):
        extract_pdf(b"", "empty.pdf")
    with pytest.raises(ValueError):
        extract_pdf(b"not a pdf", "broken.pdf")
    with pytest.raises(ValueError, match="no extractable text"):
        extract_pdf(pdf_bytes([""]), "blank.pdf")

def test_duplicate_chunk_ids_are_stable():
    content = pdf_bytes(["same source content"])
    first = extract_pdf(content, "same.pdf")
    second = extract_pdf(content, "same.pdf")
    assert [p.chunk_id for p in first] == [p.chunk_id for p in second]
