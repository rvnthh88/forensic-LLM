from pathlib import Path
import time

import streamlit as st

from core.index_stats import read_index_stats
from core.ollama_client import ollama_status


PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "data" / "chroma"
COLLECTION = "forensicllm_demo"

st.set_page_config(page_title="Digital Forensics Reference Assistant", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --page: #f1f3f5;
        --surface: #ffffff;
        --navy: #18324f;
        --ink: #243447;
        --muted: #64748b;
        --line: #d9e1e8;
        --teal: #176b70;
        --teal-hover: #12575c;
        --soft-teal: #eaf3f3;
    }
    .stApp { background: var(--page); color: var(--ink); }
    header[data-testid="stHeader"] { background: #f1f3f5; }
    .block-container { max-width: 1120px; padding-top: 1.7rem; padding-bottom: 2.4rem; }
    .eyebrow {
        margin: 0 0 0.35rem 0.05rem; color: var(--teal); font-size: 0.7rem;
        font-weight: 700; letter-spacing: 0.11em; text-transform: uppercase;
    }
    h1, h2, h3 { color: var(--navy) !important; letter-spacing: -0.02em; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: var(--navy) !important; }
    h1 {
        font-size: 2rem !important; font-weight: 680 !important; margin-bottom: 0.25rem !important;
        padding-left: 0.75rem; border-left: 3px solid var(--teal);
    }
    h2 { font-size: 1.3rem !important; font-weight: 650 !important; }
    h3 { font-size: 1.06rem !important; font-weight: 650 !important; }
    p, label, [data-testid="stMarkdownContainer"] { color: var(--ink); }
    .block-container [data-testid="stCaptionContainer"],
    .block-container [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"],
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
    [data-testid="stSidebar"] { background: #edf1f4; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] .block-container { padding-top: 1.15rem; }
    [data-testid="stMetric"] {
        background: var(--surface); border: 1px solid var(--line); border-radius: 7px;
        padding: 0.65rem 0.75rem;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--navy); font-size: 1.45rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface); border-color: var(--line); border-radius: 8px;
    }
    div.stButton > button {
        border: 1px solid #cbd6df; border-radius: 6px; color: var(--navy);
        background: var(--surface); transition: background-color 120ms ease, border-color 120ms ease;
    }
    div.stButton > button:not([kind="primary"]) {
        min-height: 3.15rem; height: auto; padding: 0.55rem 0.75rem;
        text-align: left; white-space: normal; line-height: 1.35;
        box-shadow: 0 1px 2px rgba(24, 50, 79, 0.04);
    }
    div.stButton > button p {
        color: inherit !important; white-space: normal !important; overflow: visible !important;
        text-overflow: clip !important; line-height: 1.35 !important; margin: 0 !important;
    }
    div.stButton > button:hover { border-color: var(--teal); color: var(--teal); background: #f6fbfb; }
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primaryFormSubmit"] {
        background: var(--teal); color: white; border-color: var(--teal); border-radius: 6px;
        font-weight: 600; min-height: 2.55rem;
    }
    div.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover { background: var(--teal-hover); border-color: var(--teal-hover); color: white; }
    div.stFormSubmitButton > button[kind="primaryFormSubmit"] p { color: #fff !important; font-weight: 650; }
    div[data-testid="stTextInput"] input {
        background: var(--surface); border-color: #bdcbd6; border-radius: 6px; min-height: 2.55rem;
    }
    div[data-testid="stTextInput"] input:focus { border-color: var(--teal); box-shadow: 0 0 0 1px var(--teal); }
    div[data-testid="stExpander"] { background: var(--surface); border: 1px solid var(--line); border-radius: 7px; }
    div[data-testid="stAlert"] { border-radius: 6px; border-left-color: var(--teal); }
    @media (max-width: 700px) {
        .block-container { padding: 1.1rem 1rem 2rem; }
        h1 { font-size: 1.65rem !important; }
        div.stButton > button:not([kind="primary"]) { min-height: 3rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">Forensic reference workspace</div>', unsafe_allow_html=True)
st.title("Digital Forensics Reference Assistant")
st.caption("Educational reference materials · Source passages include filenames and page references")


@st.cache_resource
def service():
    # Import Chroma and the embedding stack only after the user starts an action.
    from core.rag import ForensicRAG

    return ForensicRAG()


@st.cache_data(ttl=2)
def index_stats():
    return read_index_stats(DB_PATH, COLLECTION)


with st.sidebar:
    st.markdown("### Reference library")
    doc_count, passage_count = index_stats()
    metrics = st.columns(2)
    metrics[0].metric("Documents", doc_count if doc_count is not None else "—")
    metrics[1].metric("Passages", passage_count if passage_count is not None else "—")
    top_k = st.slider("Retrieved passages", 1, 8, 4)
    st.divider()
    uploaded = st.file_uploader("Add reference PDFs", type=["pdf"], accept_multiple_files=True)

    if st.button("Index uploaded PDFs", disabled=not uploaded, use_container_width=True):
        with st.spinner("Extracting text and indexing PDFs…"):
            try:
                msg = service().add_uploads(uploaded)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state.index_message = msg
                index_stats.clear()
                st.rerun()

    if st.button("Index educational sample pack", use_container_width=True):
        with st.spinner("Preparing and indexing sample PDFs…"):
            try:
                msg = service().index_samples()
            except Exception as exc:
                st.error(f"Could not index the educational sample pack: {exc}")
            else:
                st.session_state.index_message = msg
                index_stats.clear()
                st.rerun()

    index_message = st.session_state.pop("index_message", None)
    if index_message:
        st.success(index_message)

    with st.expander("Index maintenance"):
        st.caption("Clearing removes only this app's configured local demo collection.")
        if st.button("Clear demo index", type="secondary", use_container_width=True):
            service().clear()
            index_stats.clear()
            st.rerun()

questions = [
    "What information can Windows authentication events provide during a forensic investigation?",
    "How can process-creation logs help investigate suspicious PowerShell activity?",
    "What evidence should an investigator examine when investigating suspicious network connections?",
    "What limitations should be considered when interpreting digital forensic artifacts?",
]

st.subheader("Ask a question")
question_columns = st.columns(2, gap="small")
for i, preset in enumerate(questions):
    if question_columns[i % 2].button(preset, key=f"sample_{i}", use_container_width=True):
        st.session_state.question = preset

with st.form("question_form", clear_on_submit=False):
    input_column, ask_column = st.columns([5, 1], vertical_alignment="bottom")
    question = input_column.text_input(
        "Question",
        key="question",
        placeholder="Ask about the indexed reference documents",
        label_visibility="collapsed",
    )
    submitted = ask_column.form_submit_button("Ask", type="primary", use_container_width=True)

if submitted and question.strip():
    progress = st.empty()
    partial_answer = st.empty()
    partial_chunks = []
    last_partial_update = [0.0]
    progress.caption("Loading local search resources and retrieving relevant passages…")

    def show_answer_chunk(chunk):
        partial_chunks.append(chunk)
        now = time.monotonic()
        if now - last_partial_update[0] >= 0.35 or chunk.endswith((".", "?", "!", "\n")):
            partial_answer.markdown("**Local answer in progress**\n\n" + "".join(partial_chunks))
            last_partial_update[0] = now

    try:
        with st.spinner("Working on your question…"):
            ollama_ok, model_ok, _ = ollama_status()

            def show_answer_progress(passages, supported):
                if supported and ollama_ok and model_ok:
                    progress.caption(f"Retrieved {len(passages)} passages. The local model is preparing a concise, cited answer…")
                elif supported:
                    progress.caption(f"Retrieved {len(passages)} passages. Preparing the offline reference answer…")
                else:
                    progress.caption("Checking whether the retrieved passages provide enough support…")

            result = service().answer(
                question.strip(),
                top_k=top_k,
                use_llm=ollama_ok and model_ok,
                progress_callback=show_answer_progress,
                on_chunk=show_answer_chunk if ollama_ok and model_ok else None,
            )
    except Exception as exc:
        progress.empty()
        partial_answer.empty()
        st.error(f"The question could not be processed: {exc}")
    else:
        progress.empty()
        partial_answer.empty()
        st.subheader("Answer")
        with st.container(border=True):
            label = "Grounded in retrieved sources" if result["supported"] else "Insufficient supporting evidence"
            st.markdown(f"**{label}**")
            st.caption(result["mode"])
            st.write(result["answer"])

        st.subheader("Retrieved evidence")
        if result["passages"]:
            for item in result["passages"]:
                with st.container(border=True):
                    st.markdown(
                        f"**{item['source']}** &nbsp; · &nbsp; Page {item['page']} &nbsp; · &nbsp; "
                        f"Similarity {item['score']:.3f}"
                    )
                    st.write(item["text"])
        else:
            st.caption("No passages were available from the indexed reference documents.")
