from typing import Any

import httpx
from pydantic import BaseModel


class LlmMessage(BaseModel):
    role: str
    content: str


class LlmResponse(BaseModel):
    content: str
    raw: dict[str, Any]


class MiniMaxClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.transport = transport

    async def complete(self, messages: list[LlmMessage]) -> LlmResponse:
        payload = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60,
            transport=self.transport,
        ) as client:
            response = await client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            raw = response.json()

        content = self._extract_content(raw)
        return LlmResponse(content=content, raw=raw)

    def _extract_content(self, raw: dict[str, Any]) -> str:
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("MiniMax response did not include message content") from error

        if not isinstance(content, str) or not content:
            raise ValueError("MiniMax response did not include message content")

        return content
