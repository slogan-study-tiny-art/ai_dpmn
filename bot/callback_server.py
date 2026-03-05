"""
Минимальный HTTP-сервер для приёма callback от Kie (Nano Banana Pro) и отправки результата в Telegram.

Запуск из корня проекта:
  python -m bot.callback_server

Требуется .env: TELEGRAM_BOT_TOKEN, опционально KIE_JOBS_PATH.
Переменная KIE_CALLBACK_BASE_URL должна указывать на этот сервер (например https://your-domain.com),
чтобы бот подставлял callback_url при создании задачи.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

# проект корень для загрузки .env
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass

from aiogram import Bot
from aiogram.enums import ParseMode

from bot.job_store import get_chat_id, remove_job

try:
    from fastapi import FastAPI, Request
    from uvicorn import run
except ImportError:
    print("Установите fastapi и uvicorn: pip install fastapi uvicorn", file=sys.stderr)
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("callback")

app = FastAPI(title="Kie Banana Callback")

_bot: Bot | None = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
        _bot = Bot(token=token, parse_mode=ParseMode.HTML)
    return _bot


def _extract_image_url(body: dict) -> str | None:
    """Достать URL изображения из тела callback (формат Kie может отличаться)."""
    url = body.get("image_url") or (body.get("output") or {}).get("image_url")
    if url:
        return url
    output = body.get("output")
    if isinstance(output, dict):
        return output.get("url") or output.get("image_url")
    if isinstance(output, list) and output and isinstance(output[0], dict):
        return output[0].get("url") or output[0].get("image_url")
    return None


def _extract_job_id(body: dict) -> str | None:
    return body.get("job_id") or body.get("id") or body.get("task_id")


@app.post("/callback/kie-banana")
async def kie_banana_callback(request: Request):
    """Принять результат от Kie Banana и отправить фото пользователю в Telegram."""
    try:
        body = await request.json()
    except Exception as e:
        logger.warning("Invalid JSON body: %s", e)
        return {"ok": False, "error": "invalid json"}

    job_id = _extract_job_id(body)
    if not job_id:
        logger.warning("No job_id in body: %s", list(body.keys()))
        return {"ok": False, "error": "missing job_id"}

    chat_id = get_chat_id(str(job_id))
    if chat_id is None:
        logger.warning("Unknown job_id: %s", job_id)
        return {"ok": False, "error": "unknown job_id"}

    image_url = _extract_image_url(body)
    if not image_url:
        logger.warning("No image_url in body for job_id %s", job_id)
        remove_job(str(job_id))
        return {"ok": False, "error": "missing image_url"}

    try:
        bot = _get_bot()
        await bot.send_photo(chat_id, photo=image_url)
        remove_job(str(job_id))
        logger.info("Sent photo to chat_id=%s for job_id=%s", chat_id, job_id)
        return {"ok": True}
    except Exception as e:
        logger.exception("Failed to send photo to chat_id=%s: %s", chat_id, e)
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    port = int(os.getenv("CALLBACK_PORT", "8765"))
    run(app, host="0.0.0.0", port=port)
