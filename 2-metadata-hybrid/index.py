"""Build local Chroma index with Project 2 metadata."""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from chunker import chunk_docs_dir

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "acme_docs_v2"
EMBED_MODEL = "all-MiniLM-L6-v2"


def get_collection(reset: bool = False):
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def build_index() -> int:
    chunks = chunk_docs_dir(DOCS_DIR)
    collection = get_collection(reset=True)
    collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[c.metadata() for c in chunks],
    )
    return len(chunks)


if __name__ == "__main__":
    n = build_index()
    print(f"Indexed {n} chunks into {CHROMA_DIR} (model={EMBED_MODEL})")
