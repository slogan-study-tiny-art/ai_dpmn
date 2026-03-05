"""
Промт-инженер: доработка и изменение базового промта по комментарию пользователя через GPT 5.2 (Kie).

Используется только после того, как пользователь нажал «Описать замечания» и ввёл текст.
Первый проход — всегда базовый промт из prompt_builder без вызова LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kie_llm_client import KieLLMClient


PROMPT_ENGINEER_SYSTEM = """You are a prompt engineer for construction imagery.

Goal:
- You receive a BASE PROMPT for monolithic/foundation works and a USER REMARK.
- You must carefully integrate and apply the remark: rewrite or extend relevant parts of the prompt so the next image matches the user's request. Do not just append the remark; change the prompt text where needed.
- You ALWAYS respect the original meaning: no hallucinated floors, no new load-bearing structures, no fake construction stages.

Inputs:
- mode: "process" or "similar"
- base_prompt: the original structured prompt text (multi-line)
- user_remark: free-form text from the user describing what should be changed in the next image

Instructions:
1. Do NOT invent a new structure from scratch. Start strictly from base_prompt.
2. Preserve:
   - the overall structure (sections, allowed/forbidden changes),
   - the distinction between process and similar modes,
   - all safety constraints about construction reality.
3. Rewrite or extend relevant parts to reflect user_remark:
   - adjust what is allowed (e.g. "slightly brighter", "cleaner site", "more contrast"),
   - clarify what should change in the next generation.
4. Never relax or remove hard constraints about not adding new floors, not changing construction stage, not inventing cranes or workers that are not present.
5. Output ONLY the final prompt text, in the same style as base_prompt. No explanations, no JSON, no commentary.

If user_remark is empty or trivial, return base_prompt unchanged."""


async def refine_monolith_prompt(
    llm_client: KieLLMClient,
    model_id: str,
    mode: str,
    base_prompt: str,
    user_remark: str | None,
) -> str:
    """
    Доработать базовый промт по комментарию пользователя через GPT 5.2 (Kie).

    Если user_remark пустой или None — возвращает base_prompt без вызова LLM.
    """
    remark = (user_remark or "").strip()
    if not remark:
        return base_prompt

    user_content = f"""mode: {mode}

base_prompt:
{base_prompt}

user_remark: {remark}

Return only the final prompt text, no other text."""

    messages = [
        {"role": "system", "content": PROMPT_ENGINEER_SYSTEM},
        {"role": "user", "content": user_content},
    ]
    return await llm_client.chat(model_id, messages, reasoning_effort="high")
