"""Heading-aware chunker with Project 2 metadata schema B."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)
PRODUCT = "acme"


@dataclass
class Chunk:
    chunk_id: str
    product: str
    version: str
    source: str
    title: str
    section: str
    text: str

    def metadata(self) -> dict:
        """Chroma metadata (no raw text — text is stored as document)."""
        return {
            "product": self.product,
            "version": self.version,
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "chunk_id": self.chunk_id,
        }


def _title_from_content(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def chunk_markdown(source: str, version: str, content: str) -> list[Chunk]:
    title = _title_from_content(content, fallback=source)
    matches = list(HEADING_RE.finditer(content))
    if not matches:
        body = content.strip()
        if not body:
            return []
        return [
            Chunk(
                chunk_id=f"{source}::0",
                product=PRODUCT,
                version=version,
                source=source,
                title=title,
                section="(document)",
                text=body,
            )
        ]

    chunks: list[Chunk] = []
    preface = content[: matches[0].start()].strip()
    if preface:
        chunks.append(
            Chunk(
                chunk_id=f"{source}::pre",
                product=PRODUCT,
                version=version,
                source=source,
                title=title,
                section="(preface)",
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
                product=PRODUCT,
                version=version,
                source=source,
                title=title,
                section=heading,
                text=section,
            )
        )
    return chunks


def chunk_docs_dir(docs_dir: Path) -> list[Chunk]:
    """Expect docs/v1/*.md and docs/v2/*.md — version = parent folder name."""
    all_chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("v*/*.md")):
        version = path.parent.name  # v1 or v2
        source = f"{version}/{path.name}"
        all_chunks.extend(
            chunk_markdown(source, version, path.read_text(encoding="utf-8"))
        )
    return all_chunks


if __name__ == "__main__":
    docs = Path(__file__).resolve().parent / "docs"
    chunks = chunk_docs_dir(docs)
    print(f"Total chunks: {len(chunks)}\n")
    for c in chunks:
        meta = asdict(c)
        meta.pop("text")
        preview = c.text.replace("\n", " ")[:60]
        print(f"{meta} | {preview}…")
