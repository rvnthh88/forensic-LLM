# ForensicLLM-Inspired Digital Forensics Assistant

A small Windows-friendly, local RAG teaching demo over educational forensic reference PDFs. It is inspired by the 2025 ForensicLLM paper, but does not reproduce its specialized LLaMA 3.1 8B model, UAE-Large-V1 embeddings, RAFT with QLoRA, published metrics, or experimental results. This prototype uses all-MiniLM-L6-v2, ChromaDB, and optional Ollama llama3.2:3b generation. It is not a forensic evidence collection or authentication system.

## Requirements

- Windows 10/11
- Python 3.12 or 3.11 (64-bit); install from python.org and enable the Python launcher (`py`). The launcher prefers 3.12, then 3.11.
- Internet only for first-time Python package/model downloads
- Optional: Ollama for local LLM generation. The application retrieves and displays references without Ollama.

## Launch

From PowerShell or Command Prompt:

```bat
cd /d path\to\ForensicLLM_RAG_Demo
run.bat
```

The first run detects Python 3.12 or 3.11, creates `.venv` with that interpreter, installs requirements, and Sentence Transformers downloads `all-MiniLM-L6-v2` (roughly 90 MB) when first initialized. This is an embedding model required for retrieval. The script does not download or require an Ollama model. Streamlit launches when Ollama is absent, with an explicitly labelled offline extractive fallback.

Optional local LLM setup in a separate terminal:

1. Install Ollama from [ollama.com/download](https://ollama.com/download) and start it.
2. Review the model download before running `ollama pull llama3.2:3b`. The quantized model download is roughly 2 GB; required disk and RAM can vary.
3. Restart the app. The sidebar reports whether Ollama and the model are detected.

## Demo use

Click **Index educational sample pack** in the sidebar. The app generates three clearly labelled educational PDFs about Windows authentication, Sysmon process creation, and network forensics, then indexes their actual extracted passages. Upload additional PDF reference material from the same sidebar. Scanned image-only PDFs need OCR beforehand; OCR is not included. Password-protected and unreadable PDFs are reported as errors.

Use the sample questions or ask your own. Results show retrieved text, source, one-based PDF page, and cosine similarity (higher is closer). The default retrieval count is four. Weak matches are labelled **Insufficient Supporting Evidence**. The offline fallback uses retrieved text directly and labels itself clearly. Ollama is prompted to answer only from retrieved passages and cite their locations. All sources are educational references, not authentic case records.

The local presentation index is stored in `data/chroma`; generated PDFs are in `sample_pdfs`. The reset control deletes only the app's `forensicllm_demo` collection at that configured path. Do not manually point `DB_PATH` at unrelated Chroma data.

## Tests

```bat
cd /d path\to\ForensicLLM_RAG_Demo
.venv\Scripts\python.exe -m pytest -q
```

Integration tests construct a temporary Chroma index under pytest's temporary directory. They do not access or clear the presentation database. Tests cover extraction/page numbers, corrupt and empty PDFs, duplicate handling, retrieval, clearing, and unsupported-question fallback. To exercise the full demo manually, index the sample pack and ask the four questions below plus the unrelated cake question.

## Troubleshooting

- Python not found: install Python 3.12 or 3.11 64-bit and enable the Python launcher. WindowsApps execution aliases are ignored because they can open the Microsoft Store instead of running Python.
- If `.venv` was created by another Python installation, `run.bat` detects the different base interpreter and rebuilds the project environment with the selected Python.
- If the environment swap reports a locked file/access denied, stop the Streamlit server with `Ctrl+C` in its terminal and close IDE terminals, Python consoles, or notebooks using this project environment. Then rerun `run.bat`; the prepared `.venv.rebuild` is reused and the original `.venv` is preserved until the swap succeeds.
- If the launcher reports that `.venv.rebuild` is partial, first close the processes above, then remove only that generated staging folder from the project directory with `Remove-Item -LiteralPath .\\.venv.rebuild -Recurse`. Do not remove `core`, `scripts`, `tests`, `sample_pdfs`, or `data`.
- Package installation errors: check internet access, then run `.venv\Scripts\python -m pip install --upgrade pip` and `run.bat` again.
- First embedding initialization is slow: it downloads the MiniLM model once; keep the app open until complete.
- `Ollama unavailable`: run Ollama. Retrieval fallback remains available. If Ollama is running without the model, review the download size above and run `ollama pull llama3.2:3b` only if desired.
- PDF extraction returns no text: this build does not perform OCR. OCR the document separately before upload.
- Re-index or reset from the sidebar. Uploaded chunks are deduplicated by stable chunk ID for the same filename, page, offset, and text.

## Five-minute faculty demo

1. **0:00–0:40** Introduce the project as a local, educational RAG prototype inspired by ForensicLLM (2025), not a reproduction of the research model or results.
2. **0:40–1:10** Show the Ollama status, top-K control, and empty index counts. Explain that retrieval works without an LLM.
3. **1:10–1:45** Click **Index educational sample pack** and show the three reference documents and indexed counts.
4. **1:45–3:40** Ask the Windows authentication, PowerShell process creation, and suspicious network questions. Expand source passages and point out page numbers and relevance scores.
5. **3:40–4:20** Ask about artifact limitations and discuss why logs require context and corroboration.
6. **4:20–5:00** Ask “What is the recipe for chocolate cake?” Show **Insufficient Supporting Evidence**. Close by noting that these are educational reference sources, not findings about a real incident.

## Current scope and limitations

Retrieval quality depends on PDF text extraction and embedding similarity; a similarity threshold is a conservative heuristic, not a calibrated confidence measure. The fallback is an extractive presentation of retrieved passages. Local model output can still be mistaken, so inspect cited passages. There is no OCR, fine-tuning, evidence integrity chain, or claim that system output is verified.
