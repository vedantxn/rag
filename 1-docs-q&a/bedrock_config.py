"""Load Bedrock config from AWS Secrets Manager."""

from __future__ import annotations

import json

import boto3

SECRET_NAME = "rag/project1/bedrock"
DEFAULT_REGION = "us-east-1"


def load_bedrock_config(secret_name: str = SECRET_NAME) -> dict:
    """Return {region, model_id} from Secrets Manager."""
    sm = boto3.client("secretsmanager", region_name=DEFAULT_REGION)
    raw = sm.get_secret_value(SecretId=secret_name)["SecretString"]
    cfg = json.loads(raw)
    if "region" not in cfg or "model_id" not in cfg:
        raise ValueError(f"Secret {secret_name} must include region and model_id")
    return cfg
