"""
Клиент для Kie AI Chat Completions API (GPT 5.2 и др.).

Единый API Kie: тот же base_url и api_key, что и для Nano Banana Pro.
Endpoint: POST {base_url}/{model_id}/v1/chat/completions
Документация: https://docs.kie.ai/market/chat/gpt-5-2
"""

from __future__ import annotations

from typing import Any

import httpx


class KieLLMClient:
    """
    Обёртка над Kie AI Chat Completions (GPT 5.2 и другие LLM).

    Используется для промт-инженера: доработка/изменение промта по комментарию пользователя.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _url(self, model_id: str) -> str:
        return f"{self._base_url}/{model_id}/v1/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    async def chat(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        *,
        reasoning_effort: str = "high",
        **kwargs: Any,
    ) -> str:
        """
        Отправить запрос в Kie Chat Completions и вернуть текст ответа.

        :param model_id: id модели в Kie, например "gpt-5-2"
        :param messages: список сообщений [{"role": "system"|"user"|"assistant", "content": "..."}]
        :param reasoning_effort: "low" | "high" (для GPT 5.2)
        :return: content из choices[0].message
        """
        payload: dict[str, Any] = {
            "messages": messages,
            "reasoning_effort": reasoning_effort,
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                self._url(model_id),
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("Kie chat returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        return content.strip()
