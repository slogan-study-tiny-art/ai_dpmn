# Папка `prompts/` — промты и вызов Kie API для монолита

Здесь лежит **описание универсального промта** для монолитных работ/фундамента и **скрипт для тестового вызова Kie API** (Nano Banana Pro) без бота.

---

## Единый API Kie: промты и картинки

Всё идёт через **один API Kie** (один ключ, один базовый URL):

- **Промты и комментарии пользователя** обрабатываются моделью **GPT 5.2** в Kie (уточнение/доработка текста промта).
- **Генерация изображения** выполняется моделью **Nano Banana Pro** в Kie (по финальному промту и референсному фото).

Цепочка: базовый промт + комментарий → Kie (GPT 5.2) → уточнённый промт → Kie (Nano Banana Pro) + фото → картинка.

---

## Содержимое

| Файл | Назначение |
|------|------------|
| **PROMPTS_MONOLITH.md** | Универсальный шаблон промта на английском + список переменных. Используется как база для GPT 5.2 и как вход для Nano Banana Pro. |
| **run_kie_banana.py** | Скрипт: базовый промт + референсное фото отправляет в Kie (Nano Banana Pro) для генерации изображения. |
| **README.md** | Эта инструкция. |

---

## Переменные окружения (единый Kie)

В корне проекта в `.env`:

```env
# Единый API Kie (и GPT 5.2, и Nano Banana Pro)
KIE_API_KEY=ваш_ключ
KIE_BASE_URL=https://api.kie.ai

# Модели в Kie
KIE_LLM_MODEL=gpt-5.2
KIE_BANANA_MODEL=nano-banana-pro
```

### Запуск скрипта (тест Nano Banana Pro без бота)

Из **корня проекта**:

```bash
# Улучшить текущее фото (process)
python prompts/run_kie_banana.py process путь/к/фото.jpg

# Новое похожее фото (similar)
python prompts/run_kie_banana.py similar путь/к/фото.jpg

# С текстовым замечанием (в полном пайплайне это сначала обработает GPT 5.2)
python prompts/run_kie_banana.py process путь/к/фото.jpg "чуть ярче и контрастнее"
```

Скрипт строит базовый промт через `build_monolith_prompt(mode=..., user_remark=...)` и вызывает Kie (Nano Banana Pro) с референсным фото. Полный пайплайн с обработкой промта через GPT 5.2 в боте/агенте подключается отдельно.

---

## Универсальный промт и переменные

Полный шаблон и список переменных — в **PROMPTS_MONOLITH.md**.  
Промт-инженер при подключении новых моделей (другие версии Nano Banana Pro или другие image-модели) может:

1. Взять шаблон из `PROMPTS_MONOLITH.md`.
2. Подставить нужные значения переменных под свой пайплайн.
3. При необходимости слегка адаптировать формулировки под конкретную модель, не меняя общую структуру и ограничения (process / similar).

Готовый текст промта в коде формируется в `bot/prompt_builder.py`; для ручной подстановки переменных используйте описание из `PROMPTS_MONOLITH.md`.

---

## Клиент Kie: Nano Banana Pro (генерация картинки)

Тот же API Kie, модель Nano Banana Pro — для генерации изображения по промту и референсу.

| Что | Где |
|-----|-----|
| Клиент | `bot/kie_banana_client.py` — класс `KieBananaClient` |
| Endpoint | `POST {KIE_BASE_URL}/api/v1/jobs/createTask` |
| Промт | Базовый — `build_monolith_prompt(...)` из `bot/prompt_builder.py`; в полном пайплайне перед вызовом Banana промт обрабатывается через GPT 5.2 в Kie. |

### Пример вызова из кода

```python
from bot.kie_banana_client import KieBananaClient
from bot.prompt_builder import build_monolith_prompt

# Базовый промт (в проде его можно сначала отправить в Kie на GPT 5.2 для уточнения)
prompt = build_monolith_prompt(mode="process", user_remark="чуть ярче")
client = KieBananaClient(base_url=os.getenv("KIE_BASE_URL"), api_key=os.getenv("KIE_API_KEY"))
result = await client.create_task(
    model=os.getenv("KIE_BANANA_MODEL", "nano-banana-pro"),
    prompt=prompt,
    aspect_ratio="16:9",
    resolution="1K",
    output_format="png",
    image_paths=[path_to_reference_photo],
)
```

Клиент для вызова **GPT 5.2** через тот же Kie (обработка промтов и комментариев) добавляется отдельно при интеграции LLM в пайплайн.
