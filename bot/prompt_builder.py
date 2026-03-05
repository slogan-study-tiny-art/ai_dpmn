from __future__ import annotations

"""
Prompt construction utilities for Kei monolith/foundation image tasks.

This module is pure: it only builds text prompts and performs no I/O.
"""


def _normalize_remark(remark: str | None) -> str | None:
    """
    Normalize user remark: strip whitespace and convert empty strings to None.
    """
    if remark is None:
        return None
    cleaned = remark.strip()
    return cleaned or None


def build_monolith_prompt(
    *,
    mode: str,
    user_remark: str | None,
) -> str:
    """
    Build a universal, detailed English prompt for monolith/foundation tasks.

    Parameters:
    - mode:
        "process" — improve the existing photo without changing reality.
        "similar" — create a new image strongly inspired by the reference.
    - user_remark: additional user wishes (can be empty).
    """
    normalized_mode = (mode or "").strip().lower()
    remark = _normalize_remark(user_remark)

    if normalized_mode not in {"process", "similar"}:
        raise ValueError(f"Unsupported mode for build_monolith_prompt: {mode!r}")

    lines: list[str] = []

    # Shared context for both modes: universal, model-agnostic description
    lines.append(
        "Ultra detailed cinematic photorealistic depiction of a construction site "
        "at the monolithic works / foundation stage."
    )
    lines.append(
        "Show reinforced concrete structures, formwork and reinforcement as they really exist on the site, "
        "based on the provided reference image."
    )
    lines.append(
        "Always treat the reference image as the main source of truth for the layout of the site, "
        "the type of structure and the current construction stage."
    )
    lines.append("")

    if normalized_mode == "process":
        # Mode: improve existing photo without changing reality
        lines.append(
            "Current mode: PROCESS — improve the existing photo without changing what is actually built."
        )
        lines.append(
            "Use the input image as the base and keep all main structural elements, volumes "
            "and the construction stage exactly the same as in the reference."
        )
        lines.append("")
        lines.append("Allowed improvements:")
        lines.append(
            "- increase sharpness and clarity of existing structures and details;"
        )
        lines.append(
            "- improve exposure, contrast, dynamic range and white balance for better readability;"
        )
        lines.append(
            "- gently clean visual noise and small scattered debris on the ground, "
            "without removing important construction elements;"
        )
        lines.append(
            "- slightly refine framing and cropping if it makes the scene clearer, "
            "while still showing the same structures."
        )
        lines.append("")
        lines.append("Forbidden changes:")
        lines.append(
            "- do NOT add new load‑bearing structures, columns, beams, slabs or extra floors "
            "that are not present in the original photo;"
        )
        lines.append(
            "- do NOT change the number of floors or overall massing of the building;"
        )
        lines.append(
            "- do NOT add heavy machinery, cranes, trucks or workers that are not visible in the reference;"
        )
        lines.append(
            "- do NOT remove or radically alter major structural elements of the building under construction."
        )
    else:
        # Mode: generate a new but similar image based on the reference
        lines.append(
            "Current mode: SIMILAR — create a new image strongly inspired by the reference photo."
        )
        lines.append(
            "Use the reference as a guide for the overall layout, type of works, camera angle "
            "and main structural volumes."
        )
        lines.append("")
        lines.append("Main requirements for the new image:")
        lines.append(
            "- the new image must remain recognizably similar to the reference in terms of scene and viewpoint;"
        )
        lines.append(
            "- keep the same type of works (monolithic / foundation), the main structural elements "
            "and their relative positions;"
        )
        lines.append(
            "- preserve the general proportions and massing of the building and foundation;"
        )
        lines.append(
            "- you may make the site look cleaner, more organized and slightly idealized, "
            "in the style of a marketing or portfolio photograph."
        )
        lines.append("")
        lines.append("Hard constraints:")
        lines.append(
            "- do NOT change the construction type or stage "
            "(do not turn a foundation scene into facade finishing or a completed building);"
        )
        lines.append(
            "- do NOT add clearly new storeys or large structural volumes that significantly change the scale;"
        )
        lines.append(
            "- do NOT turn the scene into a completely different project or an unrelated location."
        )

    # Shared visual and technical guidelines
    lines.append("")
    lines.append(
        "Scene: realistic construction site environment consistent with the reference image, "
        "with clearly readable concrete, formwork and reinforcement."
    )
    lines.append(
        "Atmosphere: professional documentation / portfolio style, neutral and honest, "
        "with weather conditions that are consistent with or slightly improved compared to the reference."
    )
    lines.append(
        "Environment details: construction fences, temporary site cabins, stacks of materials, "
        "distant cranes or surrounding buildings only if they are compatible with the reference."
    )
    lines.append("")
    lines.append("Camera:")
    lines.append(
        "- cinematic or DSLR architectural camera with a 24–35mm lens;"
    )
    lines.append(
        "- eye‑level or slightly elevated angle that clearly shows the plan and depth of the foundation;"
    )
    lines.append(
        "- clean composition with sufficient depth of field so that all main structural elements are in sharp focus."
    )
    lines.append("")
    lines.append("Rendering quality:")
    lines.append(
        "ultra realistic, highly detailed, 8k resolution, professional color grading, "
        "sharp focus on concrete, rebar and formwork, realistic material textures, "
        "soft volumetric lighting and believable global illumination."
    )
    lines.append("")
    lines.append("Negative aspects to avoid:")
    lines.append(
        "blurry image, low quality, distorted or impossible structures, bent concrete elements, "
        "unrealistic deformations, extra floors that do not exist in the reference, "
        "oversaturated colors, strong artifacts, heavy motion blur, illegible scene."
    )

    if remark:
        lines.append("")
        lines.append(
            "User‑specific request (follow this carefully if provided):"
        )
        lines.append(remark)

    return "\n".join(lines)

