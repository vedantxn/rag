"""Retrieve top-k chunks from the local Chroma index (no LLM yet)."""

from __future__ import annotations

import argparse

from index import get_collection


def retrieve(query: str, k: int = 3) -> list[dict]:
    collection = get_collection(reset=False)
    result = collection.query(query_texts=[query], n_results=k)
    hits: list[dict] = []
    for i, chunk_id in enumerate(result["ids"][0]):
        hits.append(
            {
                "chunk_id": chunk_id,
                "source": result["metadatas"][0][i].get("source"),
                "heading": result["metadatas"][0][i].get("heading"),
                "distance": result["distances"][0][i] if result.get("distances") else None,
                "text": result["documents"][0][i],
            }
        )
    return hits


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve top-k chunks")
    parser.add_argument("query", type=str, help="Natural language question")
    parser.add_argument("-k", type=int, default=3, help="top-k (default 3)")
    args = parser.parse_args()

    hits = retrieve(args.query, k=args.k)
    print(f"Query: {args.query!r}  (k={args.k})\n")
    for rank, hit in enumerate(hits, start=1):
        print(f"{rank}. [{hit['chunk_id']}] {hit['heading']}  (distance={hit['distance']:.4f})")
        preview = hit["text"].replace("\n", " ")[:120]
        print(f"   {preview}…\n")
