"""
Клиент для Kie AI API: создание задач на генерацию изображений (Nano Banana Pro и др.).

Используется отдельно от KeiClient; под каждого провайдера — свой клиент.
Endpoint: POST /api/v1/jobs/createTask
"""

from __future__ import annotations

from typing import Any, Iterable

from pathlib import Path

import httpx


class KieBananaClient:
    """
    Обёртка над Kie AI API для создания задач генерации (Banana, Nano Banana Pro и т.д.).

    Base URL: например https://api.kie.ai
    Документация / пример: POST /api/v1/jobs/createTask с JSON body.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _url(self) -> str:
        return f"{self._base_url}/api/v1/jobs/createTask"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    async def create_task(
        self,
        *,
        model: str,
        prompt: str,
        aspect_ratio: str = "1:1",
        resolution: str = "1K",
        output_format: str = "png",
        callback_url: str | None = None,
        image_paths: Iterable[Path] | None = None,
        **extra_input: Any,
    ) -> dict[str, Any]:
        """
        Создать задачу на генерацию изображения в Kie AI (Banana).

        :param model: id модели, например "nano-banana-pro"
        :param prompt: текстовый промт (универсальный монолитный — из prompt_builder)
        :param aspect_ratio: соотношение сторон, например "1:1", "16:9"
        :param resolution: разрешение, например "1K"
        :param output_format: формат вывода, например "png"
        :param callback_url: URL для callback по готовности (опционально)
        :param image_paths: локальные пути к референсным изображениям (JPEG/PNG/WEBP, до 8 штук)
        :param extra_input: дополнительные поля в input (если API поддерживает)
        :return: ответ API (job id, status и т.д.)
        """
        # Если нет референсных изображений — используем JSON-запрос как в примере документации.
        if not image_paths:
            payload: dict[str, Any] = {
                "model": model,
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "output_format": output_format,
                    **extra_input,
                },
            }
            if callback_url:
                payload["callBackUrl"] = callback_url

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self._url(),
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        # Если переданы пути к изображениям — отправляем multipart с полем image_input.
        data: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "output_format": output_format,
            **extra_input,
        }
        if callback_url:
            data["callBackUrl"] = callback_url

        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for path in image_paths:
            # Kie Nano Banana Pro поддерживает JPEG, PNG, WEBP до 30MB; максимум 8 файлов.
            # Здесь мы не валидируем размер, это ответственность вызывающего кода.
            suffix = path.suffix.lower()
            if suffix in {".jpg", ".jpeg"}:
                content_type = "image/jpeg"
            elif suffix == ".png":
                content_type = "image/png"
            elif suffix == ".webp":
                content_type = "image/webp"
            else:
                content_type = "application/octet-stream"

            files.append(
                (
                    "image_input",
                    (path.name, path.read_bytes(), content_type),
                )
            )

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self._url(),
                headers={"Authorization": f"Bearer {self._api_key}"},
                data=data,
                files=files,
            )
            response.raise_for_status()
            return response.json()
