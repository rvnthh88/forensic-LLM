"""Lightweight, read-only counts for the initial UI render."""

import sqlite3
from pathlib import Path


def read_index_stats(db_path: str | Path, collection_name: str) -> tuple[int | None, int | None]:
    """Read Chroma's local metadata without importing Chroma or the ML stack."""
    database = Path(db_path) / "chroma.sqlite3"
    if not database.is_file():
        return 0, 0
    try:
        uri = database.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=0.5) as connection:
            query = (
                "SELECT COUNT(DISTINCT e.embedding_id), "
                "COUNT(DISTINCT m.string_value) "
                "FROM collections c "
                "JOIN segments s ON s.collection = c.id "
                "JOIN embeddings e ON e.segment_id = s.id "
                "LEFT JOIN embedding_metadata m ON m.id = e.id AND m.key = ? "
                "WHERE c.name = ?"
            )
            row = connection.execute(query, ("source", collection_name)).fetchone()
            return int(row[1] or 0), int(row[0] or 0)
    except sqlite3.Error:
        return None, None
