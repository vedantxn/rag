"""Hybrid retrieve with version pre-filter (Decision 2A)."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict

from index import get_collection
from versioning import resolve_version, strip_version_phrases

RRF_K = 60
DENSE_CANDIDATES = 10


def _keyword_ranks(query: str, ids: list[str], documents: list[str]) -> dict[str, int]:
    tokens = re.findall(r"[a-z0-9_]+", query.lower())
    tokens = [t for t in tokens if len(t) >= 2]
    scored: list[tuple[float, str]] = []
    for chunk_id, doc in zip(ids, documents):
        text = doc.lower()
        score = 0.0
        for tok in tokens:
            if tok not in text:
                continue
            if any(ch.isdigit() for ch in tok) or "_" in tok:
                score += 5.0
            else:
                score += 1.0
        if score > 0:
            scored.append((score, chunk_id))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return {chunk_id: rank for rank, (_, chunk_id) in enumerate(scored, start=1)}


def _rrf_fuse(*rank_lists: dict[str, int]) -> list[str]:
    scores: dict[str, float] = defaultdict(float)
    for ranks in rank_lists:
        for chunk_id, rank in ranks.items():
            scores[chunk_id] += 1.0 / (RRF_K + rank)
    return [cid for cid, _ in sorted(scores.items(), key=lambda x: -x[1])]


def _load_corpus(version: str | None):
    """Load all chunks, optionally pre-filtered by version (Chroma where)."""
    collection = get_collection(reset=False)
    where = {"version": version} if version else None
    kwargs = {"include": ["documents", "metadatas"]}
    if where:
        kwargs["where"] = where
    payload = collection.get(**kwargs)
    return collection, payload


def retrieve(
    query: str,
    k: int = 3,
    version: str | None = None,
) -> list[dict]:
    """
    Pre-filter by version (if set), then dense + keyword → RRF → top-k.
    `version` should already be resolved (explicit or parsed); pass None for all.
    """
    search_query = strip_version_phrases(query) or query
    collection, payload = _load_corpus(version)
    ids: list[str] = payload["ids"]
    if not ids:
        return []

    documents: list[str] = payload["documents"]
    metadatas: list[dict] = payload["metadatas"]
    by_id = {cid: (doc, meta) for cid, doc, meta in zip(ids, documents, metadatas)}

    n_dense = min(DENSE_CANDIDATES, len(ids))
    query_kwargs = {
        "query_texts": [search_query],
        "n_results": n_dense,
    }
    if version:
        query_kwargs["where"] = {"version": version}
    dense_result = collection.query(**query_kwargs)
    dense_ranks = {
        cid: i + 1 for i, cid in enumerate(dense_result["ids"][0])
    }
    keyword_ranks = _keyword_ranks(search_query, ids, documents)
    fused_ids = _rrf_fuse(dense_ranks, keyword_ranks)[:k]

    hits: list[dict] = []
    for cid in fused_ids:
        doc, meta = by_id[cid]
        hits.append(
            {
                "chunk_id": cid,
                "product": meta.get("product"),
                "version": meta.get("version"),
                "source": meta.get("source"),
                "title": meta.get("title"),
                "section": meta.get("section"),
                "text": doc,
                "dense_rank": dense_ranks.get(cid),
                "keyword_rank": keyword_ranks.get(cid),
            }
        )
    return hits


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2 hybrid retrieve + version filter")
    parser.add_argument("query", type=str)
    parser.add_argument("-k", type=int, default=3)
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Explicit version v1|v2 (overrides question parse)",
    )
    args = parser.parse_args()

    resolved = resolve_version(args.version, args.query)
    hits = retrieve(args.query, k=args.k, version=resolved)
    print(f"Query: {args.query!r}")
    print(f"Resolved version filter: {resolved or '(none — all versions)'}\n")
    for rank, hit in enumerate(hits, start=1):
        print(
            f"{rank}. [{hit['chunk_id']}] v={hit['version']} | {hit['section']}  "
            f"(dense={hit.get('dense_rank')} keyword={hit.get('keyword_rank')})"
        )
        preview = hit["text"].replace("\n", " ")[:100]
        print(f"   {preview}…\n")
