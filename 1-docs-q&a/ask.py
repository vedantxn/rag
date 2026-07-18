"""Naive RAG ask loop: retrieve top-3 → Bedrock generate → Sources list."""

from __future__ import annotations

import argparse

import boto3

from bedrock_config import load_bedrock_config
from retrieve import retrieve

K = 3

SYSTEM = """You are a docs assistant for Acme Cloud.
Answer ONLY using the provided context chunks.
If the context is not enough, say you don't know.
Be concise. Do not invent steps, error codes, or UI paths.
Do not include a Sources section — that is added separately."""


def build_user_prompt(question: str, hits: list[dict]) -> str:
    parts = ["Context chunks:"]
    for h in hits:
        parts.append(f"\n---\nchunk_id: {h['chunk_id']}\nheading: {h['heading']}\n{h['text']}")
    parts.append(f"\n---\nQuestion: {question}")
    return "\n".join(parts)


def generate(question: str, hits: list[dict]) -> str:
    cfg = load_bedrock_config()
    client = boto3.client("bedrock-runtime", region_name=cfg["region"])
    response = client.converse(
        modelId=cfg["model_id"],
        system=[{"text": SYSTEM}],
        messages=[
            {
                "role": "user",
                "content": [{"text": build_user_prompt(question, hits)}],
            }
        ],
        inferenceConfig={"maxTokens": 512, "temperature": 0},
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def format_sources(hits: list[dict]) -> str:
    lines = ["Sources:"]
    for h in hits:
        lines.append(f"- [{h['chunk_id']}] {h['heading']}")
    return "\n".join(lines)


def ask(question: str, k: int = K) -> str:
    hits = retrieve(question, k=k)
    answer = generate(question, hits)
    return f"{answer}\n\n{format_sources(hits)}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask the naive RAG pipeline")
    parser.add_argument("question", type=str)
    parser.add_argument("-k", type=int, default=K)
    args = parser.parse_args()
    print(ask(args.question, k=args.k))
