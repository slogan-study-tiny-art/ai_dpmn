"""
Простое хранилище job_id → chat_id для доставки результата Kie Banana в Telegram.

Используется ботом при создании задачи и callback-сервером при получении результата.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_JOBS_PATH = BASE_DIR / "data" / "kie_jobs.json"


def _jobs_path() -> Path:
    return Path(os.getenv("KIE_JOBS_PATH", str(DEFAULT_JOBS_PATH)))


def _read_all() -> dict:
    path = _jobs_path()
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_all(data: dict) -> None:
    path = _jobs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)


def add_job(job_id: str, chat_id: int) -> None:
    data = _read_all()
    data[job_id] = {"chat_id": chat_id}
    _write_all(data)


def get_chat_id(job_id: str) -> int | None:
    data = _read_all()
    rec = data.get(job_id)
    if rec is None:
        return None
    return rec.get("chat_id")


def remove_job(job_id: str) -> None:
    data = _read_all()
    if job_id in data:
        del data[job_id]
        _write_all(data)
