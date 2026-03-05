# Universal Monolith / Foundation Prompt (English)

Универсальный детализированный промт для задач по монолитным работам и фундаменту. В этом проекте используется с Nano Banana Pro (через Kie.ai).

---

## Prompt Template (with placeholders)

```
Ultra detailed {STYLE} depiction of a construction site with {MAIN_SUBJECT},
at a monolithic works / foundation stage, showing {STRUCTURE_STATE_AND_SCOPE}.

Scene set in {LOCATION_DESCRIPTION} on the construction site,
during {TIME_OF_DAY} with {LIGHTING_STYLE} lighting.

Atmosphere: {MOOD}, {WEATHER_CONDITIONS},
environment details: {ENVIRONMENT_DETAILS}.

Camera: {CAMERA_TYPE},
lens {LENS_TYPE},
angle {CAMERA_ANGLE},
depth of field, clear readable composition focusing on the structural elements.

Rendering quality: ultra realistic, highly detailed,
8k resolution, professional color grading,
sharp focus on concrete, formwork and reinforcement,
realistic materials, volumetric lighting, global illumination.

Reference usage and truthfulness:
use the provided reference image as the main source of truth for the site layout,
structure type and construction stage.
Preserve the overall scene, type of works and composition from the reference.

If mode = "process": improve the existing photo without changing reality.
Allowed improvements: {ALLOWED_IMPROVEMENTS_PROCESS}.
Forbidden changes: {FORBIDDEN_CHANGES_PROCESS}.

If mode = "similar": create a new image strongly inspired by the reference.
Keep the same type of works, similar camera angle and main volumes.
Allowed idealization: {ALLOWED_IDEALIZATION_SIMILAR}.
Forbidden changes: {FORBIDDEN_CHANGES_SIMILAR}.

Style influence: {ART_STYLE_REFERENCE}.

Additional technical details: {EXTRA_DETAILS}.

Negative aspects avoided:
blurry, low quality, bad anatomy of people, distorted structures,
bent or impossible concrete elements, extra floors,
oversaturated colors, artifacts, heavy motion blur, illegible scene.
```

---

## Variables (editable list)

### Construction / Subject

| Variable | Description | Example |
|----------|-------------|---------|
| `{MAIN_SUBJECT}` | Main focus of the frame | reinforced concrete foundation pit, monolithic slab with formwork and rebar |
| `{STRUCTURE_STATE_AND_SCOPE}` | Stage and scale of the build | freshly poured concrete slab, ground floor foundation walls under construction |

### Scene

| Variable | Description | Example |
|----------|-------------|---------|
| `{LOCATION_DESCRIPTION}` | Context of the site | urban residential construction site, open industrial site |
| `{TIME_OF_DAY}` | Time of day | early morning, noon, golden hour sunset |
| `{WEATHER_CONDITIONS}` | Weather | clear sky, light clouds, slight fog |

### Atmosphere

| Variable | Description | Example |
|----------|-------------|---------|
| `{MOOD}` | Mood | professional documentation, neutral, honest |

### Visual environment

| Variable | Description | Example |
|----------|-------------|---------|
| `{ENVIRONMENT_DETAILS}` | Background and surroundings | tower cranes in the distance, stacks of formwork panels, safety fences |

### Camera

| Variable | Description | Example |
|----------|-------------|---------|
| `{CAMERA_TYPE}` | Camera type | cinematic camera, DSLR, architectural photography camera |
| `{LENS_TYPE}` | Lens | 24mm wide angle, 35mm, 50mm |
| `{CAMERA_ANGLE}` | Viewpoint | eye-level shot, slightly elevated angle, low angle from ground level |

### Lighting

| Variable | Description | Example |
|----------|-------------|---------|
| `{LIGHTING_STYLE}` | Lighting mood | soft overcast lighting, warm golden hour, crisp daylight |

### Style

| Variable | Description | Example |
|----------|-------------|---------|
| `{STYLE}` | Overall visual style | photorealistic, cinematic, hyperrealistic |
| `{ART_STYLE_REFERENCE}` | Stylistic influence | professional architectural photography, real estate marketing |

### Mode-specific (process)

| Variable | Description |
|----------|-------------|
| `{ALLOWED_IMPROVEMENTS_PROCESS}` | Increase sharpness, improve exposure/contrast, gently clean noise, refine framing. |
| `{FORBIDDEN_CHANGES_PROCESS}` | Do not add new structures, floors, machinery or workers; do not remove major elements. |

### Mode-specific (similar)

| Variable | Description |
|----------|-------------|
| `{ALLOWED_IDEALIZATION_SIMILAR}` | Cleaner site, enhanced clarity, portfolio/marketing look, same masses and layout. |
| `{FORBIDDEN_CHANGES_SIMILAR}` | Do not change construction type/stage; do not add new storeys; do not make a different project. |

### Extra

| Variable | Description | Example |
|----------|-------------|---------|
| `{EXTRA_DETAILS}` | Particles, effects | soft dust, reflections on damp concrete, fine texture on rebar |

---

## Modes

- **process** — improve the existing photo (sharpness, light, contrast, framing) without adding or removing major elements.
- **similar** — generate a new image that strongly follows the reference in composition and type of works; may look more polished.

Готовые заполненные промты для обоих режимов строятся в коде: `bot/prompt_builder.py` → `build_monolith_prompt(mode=..., user_remark=...)`. В пайплайне через единый API Kie: промты и комментарии пользователя обрабатываются **GPT 5.2**, итоговый промт и референсное фото отправляются в **Nano Banana Pro** для генерации изображения.
