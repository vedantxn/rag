# Project 2 — Metadata + Hybrid (Design Brief)

## Goal

Same Docs Q&A idea as Project 1, but **production-shaped**:

1. Every chunk carries **metadata** (`product`, `version`, `section`, …)
2. Queries can **filter** (e.g. only `version=v2`)
3. **Hybrid retrieve** (dense + keyword/BM25 → RRF) — keep exact codes working
4. **Citation contract** — answer + Sources (same spirit as P1)

**What you learn:** version confusion + exact-string misses are the two classic prod bugs. Filters fix the first; hybrid fixes the second.

## What success looks like

- `"In v2, how do I reset API keys?"` → **v2** steps only (not v1)
- `"What is E_4022?"` → still finds the error chunk (hybrid)
- Wrong-version docs never appear in Sources when a version filter is set

## Pipeline

```
docs (with version) → chunk + metadata → embed → Chroma
query → optional version filter → hybrid retrieve → generate + Sources
```

## Design decisions

| # | Decision | Status | Choice |
|---|----------|--------|--------|
| 0 | Corpus | LOCKED | Acme docs with **v1 + v2** (deliberately different) |
| 1 | Metadata schema | LOCKED | **B —** `product`, `version`, `source`, `title`, `section`, `chunk_id` |
| 2 | How filters apply | LOCKED | **A — Pre-filter** on `version`; source = **explicit arg OR question text** |
| 3 | Hybrid details | LOCKED | **A —** dense + simple keyword + RRF (same idea as P1 hotfix) |
| 4 | Citation contract | LOCKED | **C —** full metadata in Sources list |

## Decision 1 — Metadata schema — LOCKED: B

| Field | Example | Use |
|-------|---------|-----|
| `product` | `acme` | filter / multi-product later |
| `version` | `v1` / `v2` | **main filter** this project |
| `source` | `v2/api-keys.md` | citation path |
| `title` | `API Keys (v2)` | doc title (`#` heading) |
| `section` | `Reset or rotate a key` | chunk heading |
| `chunk_id` | `v2/api-keys.md::2` | stable id |

Version is taken from the folder (`docs/v1/…`, `docs/v2/…`).

## Decision 2 — Filters — LOCKED: A (pre-filter) + both version sources

1. Resolve version:
   - **Explicit** `--version v2` wins if set
   - Else **parse** from question (`in v2`, `v1`, etc.)
   - Else no version filter (search all — fine for demos; prod often requires version)
2. **Pre-filter:** hybrid search runs only on chunks where `metadata.version` matches
3. Wrong-version docs never enter the candidate set

## Decision 3 — Hybrid — LOCKED: A

Dense (Chroma top-10) + keyword token overlap (boost exact codes) → **RRF** → top-k.  
Same pattern that fixed `E_4022` in Project 1; good enough here. BM25 can wait.

## Decision 4 — Citations — LOCKED: C

Answer first, then:

```
Sources:
- [v2/api-keys.md::2] v2 · API Keys (v2) · Reset or rotate a key
```

Shows version so you can audit that the filter worked.

## Carry-over from Project 1

- Heading-aware chunking
- Local embeds (`all-MiniLM-L6-v2`) + Chroma
- Bedrock Nova Lite via secret `rag/project1/bedrock` (reuse)
- k=3 default unless we change it

## Out of scope (Project 3+)

- Query rewrite / multi-query
- Rerank
- Token-budget packing
- Eval gold set (optional stretch)
