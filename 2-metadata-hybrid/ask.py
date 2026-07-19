"""Project 2 ask: version resolve → pre-filter hybrid → Bedrock → Sources C."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import boto3

from retrieve import retrieve
from versioning import resolve_version

K = 3


def _load_bedrock_config():
    """Load helper from Project 1 without shadowing this package's retrieve."""
    path = Path(__file__).resolve().parent.parent / "1-docs-q&a" / "bedrock_config.py"
    spec = importlib.util.spec_from_file_location("p1_bedrock_config", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.load_bedrock_config


load_bedrock_config = _load_bedrock_config()

SYSTEM = """You are a docs assistant for Acme Cloud.
Answer ONLY using the provided context chunks.
If the context is not enough, say you don't know.
Be concise. Do not invent steps, error codes, or UI paths.
Respect the version of the docs in the context (v1 vs v2 differ).
Do not include a Sources section — that is added separately."""


def build_user_prompt(question: str, hits: list[dict], version: str | None) -> str:
    parts = []
    if version:
        parts.append(f"Doc version filter: {version}")
    parts.append("Context chunks:")
    for h in hits:
        parts.append(
            f"\n---\nchunk_id: {h['chunk_id']}\n"
            f"version: {h['version']}\ntitle: {h['title']}\n"
            f"section: {h['section']}\n{h['text']}"
        )
    parts.append(f"\n---\nQuestion: {question}")
    return "\n".join(parts)


def generate(question: str, hits: list[dict], version: str | None) -> str:
    if not hits:
        return "I don't know. No matching docs were retrieved for this version/filter."
    cfg = load_bedrock_config()
    client = boto3.client("bedrock-runtime", region_name=cfg["region"])
    response = client.converse(
        modelId=cfg["model_id"],
        system=[{"text": SYSTEM}],
        messages=[
            {
                "role": "user",
                "content": [{"text": build_user_prompt(question, hits, version)}],
            }
        ],
        inferenceConfig={"maxTokens": 512, "temperature": 0},
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def format_sources(hits: list[dict]) -> str:
    lines = ["Sources:"]
    for h in hits:
        lines.append(
            f"- [{h['chunk_id']}] {h['version']} · {h['title']} · {h['section']}"
        )
    return "\n".join(lines)


def ask(question: str, k: int = K, version: str | None = None) -> str:
    resolved = resolve_version(version, question)
    hits = retrieve(question, k=k, version=resolved)
    answer = generate(question, hits, resolved)
    header = f"(version filter: {resolved or 'none'})\n\n"
    return f"{header}{answer}\n\n{format_sources(hits)}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project 2 RAG ask")
    parser.add_argument("question", type=str)
    parser.add_argument("-k", type=int, default=K)
    parser.add_argument("--version", type=str, default=None, help="v1 or v2")
    args = parser.parse_args()
    print(ask(args.question, k=args.k, version=args.version))
