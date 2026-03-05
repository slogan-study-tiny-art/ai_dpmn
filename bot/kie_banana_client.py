"""
Клиент для Kie AI API: создание задач на генерацию изображений (Nano Banana Pro и др.).

- Загрузка файлов: POST /api/file-stream-upload → получаем URL.
- Создание задачи: POST /api/v1/jobs/createTask с телом {"model": "...", "input": "<JSON-строка>"}.
  В input строка JSON с полями: image_input (массив URL), aspect_ratio, output_format, prompt, resolution.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

import httpx

logger = logging.getLogger(__name__)


class KieBananaClient:
    """
    Обёртка над Kie AI API: загрузка файлов и создание задач генерации (Nano Banana Pro).
    Base URL: один и тот же для upload и createTask (например https://api.kie.ai).
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _create_task_url(self) -> str:
        return f"{self._base_url}/api/v1/jobs/createTask"

    def _upload_url(self) -> str:
        return f"{self._base_url}/api/file-stream-upload"

    def _headers_json(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    async def _upload_file(self, path: Path, upload_path: str = "kieai/market") -> str:
        """Загрузить файл через Kie File Stream Upload, вернуть URL для image_input."""
        with path.open("rb") as f:
            file_bytes = f.read()
        file_name = path.name
        suffix = path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            content_type = "image/jpeg"
        elif suffix == ".png":
            content_type = "image/png"
        elif suffix == ".webp":
            content_type = "image/webp"
        else:
            content_type = "application/octet-stream"

        files = {"file": (file_name, file_bytes, content_type)}
        data = {"uploadPath": upload_path, "fileName": file_name}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self._upload_url(),
                headers={"Authorization": f"Bearer {self._api_key}"},
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()

        data_obj = result.get("data") or result
        url = data_obj.get("fileUrl") or data_obj.get("downloadUrl")
        if not url:
            raise ValueError(f"Upload response has no fileUrl/downloadUrl: {result}")
        logger.info("Uploaded %s -> %s", path.name, url)
        return url

    async def create_task(
        self,
        *,
        model: str,
        prompt: str,
        aspect_ratio: str = "4:3",
        resolution: str = "1K",
        output_format: str = "jpg",
        callback_url: str | None = None,
        image_paths: Iterable[Path] | None = None,
        **extra_input: Any,
    ) -> dict[str, Any]:
        """
        Создать задачу на генерацию в Kie AI (Nano Banana Pro).

        Формат тела как в логах Kie: "input" — строка JSON с полями image_input (массив URL),
        aspect_ratio, output_format, prompt, resolution.
        """
        image_urls: list[str] = []
        if image_paths:
            for p in image_paths:
                url = await self._upload_file(p)
                image_urls.append(url)

        input_obj: dict[str, Any] = {
            "image_input": image_urls,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "prompt": prompt,
            "resolution": resolution,
            **extra_input,
        }
        payload: dict[str, Any] = {
            "model": model,
            "input": json.dumps(input_obj),
        }
        if callback_url:
            payload["callBackUrl"] = callback_url

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                self._create_task_url(),
                headers=self._headers_json(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()
