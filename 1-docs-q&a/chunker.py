"""Heading-aware chunker for Project 1 (Decision B)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    chunk_id: str
    source: str
    heading: str
    text: str


def chunk_markdown(source: str, content: str) -> list[Chunk]:
    """Split markdown on # / ## headings. Each section becomes one chunk."""
    matches = list(HEADING_RE.finditer(content))
    if not matches:
        # No headings — whole file is one chunk
        body = content.strip()
        if not body:
            return []
        return [
            Chunk(
                chunk_id=f"{source}::0",
                source=source,
                heading="(document)",
                text=body,
            )
        ]

    chunks: list[Chunk] = []
    # Prefatory text before the first heading (rare)
    preface = content[: matches[0].start()].strip()
    if preface:
        chunks.append(
            Chunk(
                chunk_id=f"{source}::pre",
                source=source,
                heading="(preface)",
                text=preface,
            )
        )

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section = content[start:end].strip()
        heading = match.group(2).strip()
        chunks.append(
            Chunk(
                chunk_id=f"{source}::{i}",
                source=source,
                heading=heading,
                text=section,
            )
        )
    return chunks


def chunk_docs_dir(docs_dir: Path) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*.md")):
        all_chunks.extend(chunk_markdown(path.name, path.read_text(encoding="utf-8")))
    return all_chunks


if __name__ == "__main__":
    docs = Path(__file__).resolve().parent / "docs"
    chunks = chunk_docs_dir(docs)
    print(f"Total chunks: {len(chunks)}\n")
    for c in chunks:
        preview = c.text.replace("\n", " ")[:80]
        print(f"[{c.chunk_id}] {c.heading}")
        print(f"  {preview}…\n")
