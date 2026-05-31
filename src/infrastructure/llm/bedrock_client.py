"""Cliente AWS Bedrock (modelos Claude vía boto3, adapta el port).

Usa la Messages API de Anthropic sobre Bedrock (`invoke_model`). Credenciales
AWS por env. Import de boto3 diferido al uso.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import structlog

from src.application.ports import LargeLanguageModel
from src.domain.entities import ChatMessage

log = structlog.get_logger(__name__)


class BedrockClient(LargeLanguageModel):
    def __init__(
        self,
        model_id: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str = "us-east-1",
        max_tokens: int = 1024,
    ) -> None:
        if not (aws_access_key_id and aws_secret_access_key):
            raise ValueError("Credenciales AWS vacías: no se puede instanciar BedrockClient")
        import boto3

        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self._model_id = model_id
        self._max_tokens = max_tokens

    def _body(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        role_map = {"user": "user", "assistant": "assistant", "system": "user"}
        msgs = [{"role": role_map.get(m.role, "user"), "content": m.content} for m in messages]
        return json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self._max_tokens,
                "system": system_prompt,
                "messages": msgs,
            }
        )

    def generate(self, system_prompt: str, messages: list[ChatMessage]) -> str:
        resp = self._client.invoke_model(
            modelId=self._model_id, body=self._body(system_prompt, messages)
        )
        payload = json.loads(resp["body"].read())
        return "".join(b.get("text", "") for b in payload.get("content", []))

    def stream(self, system_prompt: str, messages: list[ChatMessage]) -> Iterator[str]:
        resp = self._client.invoke_model_with_response_stream(
            modelId=self._model_id, body=self._body(system_prompt, messages)
        )
        for event in resp["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk.get("type") == "content_block_delta":
                text = chunk.get("delta", {}).get("text")
                if text:
                    yield text
