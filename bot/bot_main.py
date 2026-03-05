import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from bot import shared_data
from bot.kie_banana_client import KieBananaClient
from bot.kie_llm_client import KieLLMClient
from bot.monolith_flow import router as monolith_router


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


def load_config() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")
    kie_api_key = (os.getenv("KIE_API_KEY") or "").strip()
    kie_base_url = (os.getenv("KIE_BASE_URL") or "https://api.kie.ai").strip()
    kie_llm_model = (os.getenv("KIE_LLM_MODEL") or "gpt-5-2").strip()
    kie_banana_model = (os.getenv("KIE_BANANA_MODEL") or "nano-banana-pro").strip()
    return {
        "token": token,
        "kie_api_key": kie_api_key,
        "kie_base_url": kie_base_url,
        "kie_llm_model": kie_llm_model,
        "kie_banana_model": kie_banana_model,
    }


async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Я бот для работы с референсами строительной компании.\n\n"
        "Сейчас доступен режим:\n"
        "• <b>Монолит / фундамент</b> — обработка текущего фото или генерация нового, но похожего (команда /monolith).\n\n"
        "Чтобы начать, отправь команду /monolith и следуй инструкциям.",
        parse_mode=ParseMode.HTML,
    )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = load_config()
    bot = Bot(
        token=config["token"],
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    if config["kie_api_key"]:
        shared_data.kie_banana_client = KieBananaClient(
            base_url=config["kie_base_url"],
            api_key=config["kie_api_key"],
        )
        shared_data.kie_llm_client = KieLLMClient(
            base_url=config["kie_base_url"],
            api_key=config["kie_api_key"],
        )
        shared_data.kie_llm_model = config["kie_llm_model"]
        shared_data.kie_banana_model = config["kie_banana_model"]
    else:
        shared_data.kie_banana_client = None
        shared_data.kie_llm_client = None
        shared_data.kie_llm_model = None
        shared_data.kie_banana_model = None

    dp.include_router(monolith_router)
    dp.message.register(handle_start, CommandStart())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

