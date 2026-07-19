"""Retrieve top-k chunks: dense (Chroma) + keyword, fused with RRF.

Why hybrid here: pure vectors miss exact tokens like E_4022.
Keyword search catches those; dense still handles paraphrases.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict

from index import get_collection

# RRF constant (standard default)
RRF_K = 60
# Pull a wider dense net, then fuse down to final k
DENSE_CANDIDATES = 10


def _hit_from_meta(chunk_id: str, document: str, metadata: dict, **extra) -> dict:
    return {
        "chunk_id": chunk_id,
        "source": metadata.get("source"),
        "heading": metadata.get("heading"),
        "text": document,
        **extra,
    }


def _dense_ranks(collection, query: str, n: int) -> dict[str, int]:
    """chunk_id -> 1-based rank from vector search."""
    result = collection.query(query_texts=[query], n_results=n)
    ranks: dict[str, int] = {}
    for i, chunk_id in enumerate(result["ids"][0]):
        ranks[chunk_id] = i + 1
    return ranks


def _keyword_ranks(query: str, ids: list[str], documents: list[str]) -> dict[str, int]:
    """
    Rank chunks by exact-ish token overlap (case-insensitive).
    Tokens like e_4022 get a strong boost when present in the chunk text.
    """
    tokens = re.findall(r"[a-z0-9_]+", query.lower())
    tokens = [t for t in tokens if len(t) >= 2]

    scored: list[tuple[float, str]] = []
    for chunk_id, doc in zip(ids, documents):
        text = doc.lower()
        score = 0.0
        for tok in tokens:
            if tok not in text:
                continue
            # Exact codes / ids (contain digit or underscore) matter more
            if any(ch.isdigit() for ch in tok) or "_" in tok:
                score += 5.0
            else:
                score += 1.0
        if score > 0:
            scored.append((score, chunk_id))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return {chunk_id: rank for rank, (_, chunk_id) in enumerate(scored, start=1)}


def _rrf_fuse(*rank_lists: dict[str, int]) -> list[str]:
    """Reciprocal Rank Fusion → ordered chunk_ids (best first)."""
    scores: dict[str, float] = defaultdict(float)
    for ranks in rank_lists:
        for chunk_id, rank in ranks.items():
            scores[chunk_id] += 1.0 / (RRF_K + rank)
    return [cid for cid, _ in sorted(scores.items(), key=lambda x: -x[1])]


def retrieve(query: str, k: int = 3) -> list[dict]:
    collection = get_collection(reset=False)
    payload = collection.get(include=["documents", "metadatas"])
    ids: list[str] = payload["ids"]
    documents: list[str] = payload["documents"]
    metadatas: list[dict] = payload["metadatas"]
    by_id = {
        cid: (doc, meta) for cid, doc, meta in zip(ids, documents, metadatas)
    }

    n_dense = min(DENSE_CANDIDATES, len(ids))
    dense = _dense_ranks(collection, query, n=n_dense)
    keyword = _keyword_ranks(query, ids, documents)
    fused_ids = _rrf_fuse(dense, keyword)[:k]

    hits: list[dict] = []
    for cid in fused_ids:
        doc, meta = by_id[cid]
        hits.append(
            _hit_from_meta(
                cid,
                doc,
                meta,
                dense_rank=dense.get(cid),
                keyword_rank=keyword.get(cid),
            )
        )
    return hits


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve top-k chunks (hybrid)")
    parser.add_argument("query", type=str, help="Natural language question")
    parser.add_argument("-k", type=int, default=3, help="top-k (default 3)")
    args = parser.parse_args()

    hits = retrieve(args.query, k=args.k)
    print(f"Query: {args.query!r}  (k={args.k}, hybrid=dense+keyword RRF)\n")
    for rank, hit in enumerate(hits, start=1):
        print(
            f"{rank}. [{hit['chunk_id']}] {hit['heading']}  "
            f"(dense={hit.get('dense_rank')} keyword={hit.get('keyword_rank')})"
        )
        preview = hit["text"].replace("\n", " ")[:120]
        print(f"   {preview}…\n")
