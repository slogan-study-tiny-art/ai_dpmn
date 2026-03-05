import logging
import os
from pathlib import Path
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot import shared_data
from bot.job_store import add_job
from bot.prompt_builder import build_monolith_prompt
from bot.prompt_engineer import refine_monolith_prompt


BASE_DIR = Path(__file__).resolve().parent
MONOLITH_UPLOAD_DIR = BASE_DIR / "uploads" / "monolith"

router = Router(name="monolith")


class MonolithStates(StatesGroup):
    waiting_file = State()
    waiting_mode = State()
    waiting_remark = State()
    processing = State()


def _mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Обработать текущее фото",
                    callback_data="monolith:mode:process",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Новое, но похожее",
                    callback_data="monolith:mode:similar",
                )
            ],
        ]
    )


def _approval_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подходит",
                    callback_data="monolith:ok",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Описать замечания",
                    callback_data="monolith:remark",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Перегенерировать",
                    callback_data="monolith:regen",
                )
            ],
        ]
    )


async def _save_monolith_file(bot: Bot, message: Message) -> Optional[Path]:
    if not message.photo and not message.document:
        return None

    user_id = message.from_user.id
    user_dir = MONOLITH_UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    if message.photo:
        file_obj = message.photo[-1]
        ext = ".jpg"
        file_name = f"monolith_{file_obj.file_id}{ext}"
    else:
        file_obj = message.document
        file_name = file_obj.file_name or f"monolith_{file_obj.file_id}"

    file_path = user_dir / file_name

    tg_file = await bot.get_file(file_obj.file_id)
    await bot.download(tg_file, destination=file_path)

    logging.info("Saved monolith file from user %s to %s", user_id, file_path)
    return file_path


@router.message(Command("monolith"))
async def monolith_start(message: Message, state: FSMContext) -> None:
    MONOLITH_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    await state.set_state(MonolithStates.waiting_file)
    await state.update_data(
        file_path=None,
        mode=None,
        remark=None,
    )

    await message.answer(
        "Режим: <b>Монолитные работы / фундамент</b>.\n\n"
        "Отправь <b>одно фото</b>, на основе которого будем работать "
        "(подготовить текущее или сделать новое, но похожее).",
    )


@router.message(MonolithStates.waiting_file)
async def monolith_collect_file(message: Message, state: FSMContext) -> None:
    path = await _save_monolith_file(message.bot, message)
    if not path:
        await message.answer("Пока принимаю только фото и документы.")
        return

    await state.update_data(file_path=str(path))
    await state.set_state(MonolithStates.waiting_mode)

    await message.answer(
        "Что делаем с этим изображением?\n\n"
        "— <b>Обработать текущее</b> (улучшить качество, свет, кадрирование и т.п.)\n"
        "— <b>Сделать новое, но похожее</b> (по композиции/сюжету)",
        reply_markup=_mode_keyboard(),
    )


@router.callback_query(MonolithStates.waiting_mode, F.data.startswith("monolith:mode:"))
async def monolith_choose_mode(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, mode = callback.data.split(":", 2)
    if mode not in {"process", "similar"}:
        await callback.answer("Неизвестный режим.", show_alert=True)
        return

    await state.update_data(mode=mode)
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(MonolithStates.processing)

    await _start_processing(callback.message, state, initial=True)


async def _start_processing(
    message: Message,
    state: FSMContext,
    initial: bool = False,
) -> None:
    data = await state.get_data()
    file_path_str: Optional[str] = data.get("file_path")
    mode: Optional[str] = data.get("mode")
    remark: Optional[str] = data.get("remark")

    if not file_path_str or not mode:
        await message.answer(
            "Не найдено изображение или режим обработки. Запусти /monolith ещё раз."
        )
        await state.clear()
        return

    current_path = Path(file_path_str)
    chat_id = message.chat.id

    if initial:
        await message.answer(
            "Начинаю обработку выбранного изображения монолитных работ/фундамента.\n"
            "После результата можно будет его утвердить, описать замечания или запросить перегенерацию.",
        )

    await message.answer(
        "Текущее исходное фото:\n"
        f"`{current_path}`",
        parse_mode="Markdown",
    )

    banana_client = shared_data.kie_banana_client
    llm_client = shared_data.kie_llm_client
    banana_model = shared_data.kie_banana_model or "nano-banana-pro"
    llm_model = shared_data.kie_llm_model or "gpt-5-2"

    base_prompt = build_monolith_prompt(mode=mode, user_remark=None)
    if remark and llm_client:
        try:
            await message.answer("Учитываю замечания через промт-инженера (GPT 5.2)...")
            prompt = await refine_monolith_prompt(
                llm_client, llm_model, mode, base_prompt, remark
            )
        except Exception:  # noqa: BLE001
            logging.exception("Prompt engineer (GPT 5.2) failed; using base prompt")
            prompt = base_prompt
    else:
        prompt = base_prompt

    if not banana_client:
        await message.answer(
            "Kie API не настроен (нет KIE_API_KEY). Задача и файл сохранены на сервере.\n\n"
            "Можешь описать замечания или отметить, что результат подходит.",
            reply_markup=_approval_keyboard(),
        )
        return

    callback_base = (os.getenv("KIE_CALLBACK_BASE_URL") or "").strip()
    callback_url = f"{callback_base.rstrip('/')}/callback/kie-banana" if callback_base else None

    try:
        result = await banana_client.create_task(
            model=banana_model,
            prompt=prompt,
            aspect_ratio="1:1",
            resolution="1K",
            output_format="png",
            image_paths=[current_path],
            callback_url=callback_url,
        )
    except Exception:  # noqa: BLE001
        logging.exception("Kie Banana create_task failed")
        await message.answer(
            "Ошибка при отправке задачи в Kie (Nano Banana Pro). Попробуйте позже или опишите замечания.",
            reply_markup=_approval_keyboard(),
        )
        return

    job_id = result.get("job_id") or result.get("id") or result.get("task_id")
    if job_id:
        add_job(str(job_id), chat_id)

    await message.answer(
        "Задача отправлена в генерацию (Nano Banana Pro). "
        "Результат придёт отдельным сообщением, когда изображение будет готово.\n\n"
        "Можешь уже сейчас описать замечания для перегенерации или отметить, что результат подходит.",
        reply_markup=_approval_keyboard(),
    )


@router.callback_query(MonolithStates.processing, F.data == "monolith:ok")
async def monolith_ok(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    file_path_str: Optional[str] = data.get("file_path")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Результат отмечен как подходящий.")

    text_lines = [
        "Задача по этому изображению завершена.",
    ]
    if file_path_str:
        text_lines.append(
            f"Исходный файл сохранён по пути:\n`{file_path_str}`",
        )
    text_lines.append(
        "\nЕсли нужно обработать ещё одно фото — просто вызови команду /monolith.",
    )

    await callback.message.answer(
        "\n".join(text_lines),
        parse_mode="Markdown",
    )
    await state.clear()


@router.callback_query(MonolithStates.processing, F.data == "monolith:regen")
async def monolith_regen(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Перегенерирую текущее изображение...")
    await callback.message.edit_reply_markup(reply_markup=None)
    await _start_processing(callback.message, state, initial=False)


@router.callback_query(MonolithStates.processing, F.data == "monolith:remark")
async def monolith_remark_request(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(MonolithStates.waiting_remark)
    await callback.message.answer(
        "Опиши, пожалуйста, что нужно исправить или изменить в результате одним сообщением.\n"
        "Эти замечания увидит промт-инженер/модель при следующей генерации.",
    )


@router.message(MonolithStates.waiting_remark, F.text)
async def monolith_save_remark_and_regen(message: Message, state: FSMContext) -> None:
    await state.update_data(remark=message.text)
    await state.set_state(MonolithStates.processing)

    await message.answer(
        "Спасибо, принял замечания. Попробую перегенерировать результат с учётом твоего комментария.",
    )
    await _start_processing(message, state, initial=False)

