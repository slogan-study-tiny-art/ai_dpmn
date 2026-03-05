"""
Скрипт для тестового вызова Kie AI Banana (createTask) с универсальным монолитным промтом
и референсным фото.

Запуск из корня проекта:
  python prompts/run_kie_banana.py process путь/к/фото.jpg
  python prompts/run_kie_banana.py similar путь/к/фото.jpg "чуть ярче"

Требуется .env: KIE_API_KEY, KIE_BASE_URL, опционально KIE_BANANA_MODEL.
Референсное фото передаётся в поле image_input (Nano Banana Pro: см. https://kie.ai/ru/nano-banana-pro).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from dotenv import load_dotenv
    load_dotenv(_project_root / ".env")
except ImportError:
    pass

from bot.kie_banana_client import KieBananaClient
from bot.prompt_builder import build_monolith_prompt


def _parse_args() -> tuple[str, Path, str | None]:
    if len(sys.argv) < 3:
        print(
            "Usage: python prompts/run_kie_banana.py <process|similar> <image_path> [remark]",
            file=sys.stderr,
        )
        sys.exit(1)
    mode = sys.argv[1].strip().lower()
    if mode not in ("process", "similar"):
        print("Mode must be 'process' or 'similar'", file=sys.stderr)
        sys.exit(1)
    image_path = Path(sys.argv[2])
    if not image_path.is_file():
        print(f"File not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    remark = sys.argv[3].strip() if len(sys.argv) > 3 else None
    return mode, image_path, remark or None


async def main() -> None:
    mode, image_path, remark = _parse_args()

    api_key = (os.getenv("KIE_API_KEY") or "").strip()
    base_url = (os.getenv("KIE_BASE_URL") or "https://api.kie.ai").strip()
    model = (os.getenv("KIE_BANANA_MODEL") or "nano-banana-pro").strip()

    if not api_key:
        print("KIE_API_KEY is not set in .env", file=sys.stderr)
        sys.exit(1)

    prompt = build_monolith_prompt(mode=mode, user_remark=remark)
    client = KieBananaClient(base_url=base_url, api_key=api_key)

    print("Calling Kie AI createTask (Banana)...")
    print(f"  model: {model}")
    print(f"  mode: {mode}")
    print(f"  image: {image_path}")
    if remark:
        print(f"  remark: {remark}")
    print()

    try:
        result = await client.create_task(
            model=model,
            prompt=prompt,
            aspect_ratio="1:1",
            resolution="1K",
            output_format="png",
            image_paths=[image_path],
        )
        print("Response:")
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
