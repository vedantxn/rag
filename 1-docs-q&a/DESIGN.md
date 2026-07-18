# Project 1 — Naive Docs Q&A (Design Brief)

## Goal

A minimal RAG pipeline:

**docs → chunk → embed → store → retrieve top-k → generate answer + citations**

No hybrid search, no rerank, no query rewrite. Those come in later projects.

## What success looks like

Ask a question about our docs → get an answer grounded in retrieved chunks → see which chunk IDs were used.

## Pipeline (naive)

```
[docs/*.md]
    → parse (read markdown)
    → chunk (DECISION 1)
    → embed (local or API embedding model)
    → vector store (local, e.g. Chroma)
    → on query: embed(query) → top-k chunks
    → pack into prompt
    → LLM generates answer + cites chunk ids
```

## Design decisions

| # | Decision | Status | Choice |
|---|----------|--------|--------|
| 0 | Corpus | LOCKED | Fake product "Acme Cloud" — 4 markdown docs |
| 1 | Chunk strategy | LOCKED | **B — Heading-aware** (split on `#` / `##`) |
| 2 | Embedding + store | LOCKED | **A — Local:** `all-MiniLM-L6-v2` + Chroma on disk |
| 3 | top-k | LOCKED | **k=3** |
| 4 | Citation format | LOCKED | **B — Sources list** after the answer |
| 5 | Generation LLM | LOCKED | **AWS Bedrock** `amazon.nova-lite-v1:0` (us-east-1) |

## Decision 1 — Chunk strategy — LOCKED: B

Split on markdown headings (`#`, `##`). Each section = one chunk.  
Include the heading text in the chunk. Tag each chunk with `source` (filename) + `chunk_id`.

**Why B:** short docs, clear headings → natural answer units.

## Decision 2 — Embedding + store — LOCKED: A (local)

- **Embed:** `sentence-transformers` model `all-MiniLM-L6-v2` (runs on your machine)
- **Store:** Chroma persistent dir `./chroma_db`
- Same model embeds docs at index time and queries at search time

**Why A:** learn the full loop with no embed API; re-index is cheap on 19 chunks.

## Decision 3 — top-k — LOCKED: 3

Retrieve 3 chunks per query. Enough for this small corpus; keeps the prompt tight.

## Decision 4 — Citations — LOCKED: B

Answer text first, then a **Sources:** block listing `chunk_id` + heading (no inline cite spam).

## Decision 5 — Generation — LOCKED: AWS Bedrock

- **Model:** `amazon.nova-lite-v1:0` (cheap, solid for grounded Q&A)
- **Region:** `us-east-1`
- **Config secret:** `rag/project1/bedrock` in AWS Secrets Manager  
  (`{"region":"us-east-1","model_id":"amazon.nova-lite-v1:0"}`)
- Auth: AWS CLI / default credential chain (no API keys in the repo)

## Out of scope (on purpose)

- Metadata filters / versions
- Hybrid (BM25 + vector)
- Rerank / query rewrite
- Fancy UI
