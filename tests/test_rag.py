"""Integration checks use a temporary Chroma directory, never the presentation index."""
import pymupdf as fitz
import pytest

import chromadb  # noqa: F401 - fail loudly when the installed RAG stack is incomplete.
import sentence_transformers  # noqa: F401
from core.rag import ForensicRAG
from core.processor import extract_pdf
from core import rag as rag_module
from core.ollama_client import ollama_status

@pytest.fixture
def rag(tmp_path):
    return ForensicRAG(db_path=tmp_path / "isolated-test-index")

def make_pdf(text):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    return doc.tobytes()

def test_index_search_duplicate_and_clear_are_isolated(rag):
    passages = extract_pdf(make_pdf("Windows event 4624 records successful logon. Event 4625 records failed logon."), "auth.pdf")
    assert rag._add(passages) == 1
    assert rag._add(passages) == 0
    hits = rag.retrieve("successful Windows logon event", top_k=4)
    assert hits and hits[0]["source"] == "auth.pdf" and hits[0]["page"] == 1
    rag.clear()
    assert rag.stats() == {"documents": 0, "passages": 0}

def test_unrelated_question_is_insufficient_and_llm_is_never_required(rag):
    rag._add(extract_pdf(make_pdf("Event 1 records process creation."), "sysmon.pdf"))
    result = rag.answer("What is the recipe for chocolate cake?", use_llm=False)
    assert result["supported"] is False, result["passages"]
    assert "insufficient" in result["mode"].lower()

def test_ollama_unavailable_is_reported_and_generation_failure_falls_back(rag, monkeypatch):
    import urllib.request
    def offline(*args, **kwargs):
        raise OSError("connection refused")
    monkeypatch.setattr(urllib.request, "urlopen", offline)
    available, installed, _ = ollama_status()
    assert (available, installed) == (False, False)
    rag._add(extract_pdf(make_pdf("Event ID 4624 records a successful Windows logon."), "auth.pdf"))
    def fail_generation(_prompt):
        raise OSError("Ollama stopped")
    monkeypatch.setattr(rag_module, "generate", fail_generation)
    result = rag.answer("What does Windows event 4624 record?", use_llm=True)
    assert result["supported"]
    assert "fallback" in result["mode"].lower()
    assert "auth.pdf" in result["answer"]
