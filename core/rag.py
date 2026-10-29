from pathlib import Path

import chromadb

from core.processor import extract_pdf
from core.samples import generate_samples
from core.ollama_client import generate

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "chroma"
SAMPLE_PATH = Path(__file__).resolve().parents[1] / "sample_pdfs"
COLLECTION = "forensicllm_demo"
# Cosine distance is 1 - cosine similarity; use a stricter cutoff so topical
# but unrelated passages (e.g. a cake question vs. process logging) are rejected.
WEAK_DISTANCE = 0.80

class ForensicRAG:
    def __init__(self, db_path=DB_PATH):
        # Delay the large embedding stack and model download until a user indexes
        # a PDF or asks a question. Opening the local Chroma index is also lazy
        # at the app layer via st.cache_resource.
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
        self._model = None

    def _encode(self, texts):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        return self._model.encode(texts).tolist()

    def stats(self):
        records = self.collection.get(include=["metadatas"])
        metas = records.get("metadatas") or []
        return {"documents": len({m["source"] for m in metas}), "passages": len(metas)}

    def _add(self, passages):
        if not passages:
            return 0
        existing = set(self.collection.get(include=[]).get("ids", []))
        fresh = [p for p in passages if p.chunk_id not in existing]
        if fresh:
            self.collection.add(ids=[p.chunk_id for p in fresh], documents=[p.text for p in fresh], metadatas=[{"source": p.source, "page": p.page} for p in fresh], embeddings=self._encode([p.text for p in fresh]))
        return len(fresh)

    def add_uploads(self, uploads):
        added = 0
        for upload in uploads:
            try:
                added += self._add(extract_pdf(upload.getvalue(), Path(upload.name).name))
            except ValueError as exc:
                raise ValueError(f"{upload.name}: {exc}") from exc
        return f"Added {added} new passages. Existing duplicate chunks were skipped."

    def index_samples(self):
        added = 0
        for path in generate_samples(SAMPLE_PATH):
            added += self._add(extract_pdf(path.read_bytes(), path.name))
        return f"Sample pack ready; indexed {added} new passages."

    def retrieve(self, question, top_k=4):
        if self.collection.count() == 0:
            return []
        vector = self._encode([question])
        result = self.collection.query(query_embeddings=vector, n_results=min(top_k, self.collection.count()), include=["documents", "metadatas", "distances"])
        passages = []
        for text, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
            passages.append({"text": text, "source": meta["source"], "page": meta["page"], "score": max(0.0, 1.0 - float(distance)), "distance": float(distance)})
        return passages

    def answer(self, question, top_k=4, use_llm=False, progress_callback=None, on_chunk=None):
        passages = self.retrieve(question, top_k)
        supported = bool(passages) and passages[0]["distance"] <= WEAK_DISTANCE
        if progress_callback:
            progress_callback(passages, supported)
        if not supported:
            answer = "The indexed reference documents did not provide sufficiently relevant support for a reliable answer. Review the retrieved passages below, add appropriate references, or refine the question."
            return {"answer": answer, "supported": False, "mode": "Offline retrieval fallback — insufficient supporting evidence.", "passages": passages}
        if use_llm:
            evidence = "\n\n".join(f"[{p['source']}, p. {p['page']}] {p['text']}" for p in passages)
            prompt = ("Answer only from the supplied educational reference passages. Give a concise answer in about 80–120 words, citing filenames and pages. Do not infer case findings. If support is insufficient, say so.\n\n" + f"QUESTION: {question}\n\nPASSAGES:\n{evidence}\n\nANSWER:")
            try:
                answer = generate(prompt) if on_chunk is None else generate(prompt, on_chunk=on_chunk)
                if not answer:
                    raise RuntimeError("Ollama returned an empty response")
                mode = "Generated locally by Ollama llama3.2:3b from retrieved reference passages."
            except Exception:
                answer, mode = self._fallback(passages), "Offline retrieval fallback — Ollama request failed; no LLM answer was used."
        else:
            answer, mode = self._fallback(passages), "Offline retrieval fallback — extractive synthesis from indexed passages; no LLM was used."
        return {"answer": answer, "supported": True, "mode": mode, "passages": passages}

    @staticmethod
    def _fallback(passages):
        return "Based on the retrieved educational reference passages:\n\n" + "\n\n".join(f"• {p['text']} [{p['source']}, p. {p['page']}]" for p in passages)

    def clear(self):
        self.client.delete_collection(COLLECTION)
        self.collection = self.client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
