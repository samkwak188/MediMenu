from __future__ import annotations

import base64
import io
import json
import re
from typing import Any

from openai import OpenAI
from PIL import Image
from pydantic import ValidationError

from ..config import get_settings
from ..prompts import (
    B2B_SYSTEM_PROMPT,
    MENU_ANALYSIS_JSON_SCHEMA,
    SYSTEM_PROMPT,
    build_restaurant_prompt,
    build_user_prompt,
)
from ..schemas import MenuAnalysisModel

# Lazy-import OCR to avoid loading torch/EasyOCR on every server start
def _lazy_ocr():
    from .text_finder import detect_text_regions, match_dishes_to_ocr
    return detect_text_regions, match_dishes_to_ocr

MAX_IMAGE_DIMENSION = 1024  # px — resize large photos before sending to GPT

_CLIENT: OpenAI | None = None


def _get_client() -> OpenAI:
    global _CLIENT
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is missing.")
    if _CLIENT is None:
        _CLIENT = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
        )
    return _CLIENT


def _downscale_image(image_base64: str, mime_type: str) -> tuple[str, str]:
    """Resize image to MAX_IMAGE_DIMENSION if larger. Returns (base64, mime)."""
    raw = base64.b64decode(image_base64)
    img = Image.open(io.BytesIO(raw))
    w, h = img.size
    if max(w, h) <= MAX_IMAGE_DIMENSION:
        return image_base64, mime_type
    ratio = MAX_IMAGE_DIMENSION / max(w, h)
    new_size = (int(w * ratio), int(h * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode(), "image/jpeg"


def _strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_text_from_response(response: Any) -> str:
    output_parsed = getattr(response, "output_parsed", None)
    if isinstance(output_parsed, dict):
        return json.dumps(output_parsed)

    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    if hasattr(response, "model_dump"):
        data = response.model_dump()
    elif isinstance(response, dict):
        data = response
    else:
        data = {}

    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"].strip()

    if isinstance(data.get("output_parsed"), dict):
        return json.dumps(data["output_parsed"])

    for output_item in data.get("output", []):
        for content_item in output_item.get("content", []):
            if isinstance(content_item.get("text"), str) and content_item["text"].strip():
                return content_item["text"].strip()

    raise ValueError("OpenAI response did not contain any text output.")


def _request_structured_analysis(
    image_base64: str,
    mime_type: str,
    allergies: list[str],
    medications: list[str],
    dietary_restrictions: list[str] | None = None,
    retry_hint: str | None = None,
    *,
    system_prompt: str = SYSTEM_PROMPT,
    user_prompt_override: str | None = None,
) -> MenuAnalysisModel:
    settings = get_settings()
    client = _get_client()
    if user_prompt_override:
        user_prompt = user_prompt_override
    else:
        user_prompt = build_user_prompt(
            allergies=allergies,
            medications=medications,
            dietary_restrictions=dietary_restrictions,
        )
    if retry_hint:
        user_prompt = f"{user_prompt}\n\n{retry_hint}"

    # Send the ORIGINAL image to GPT (no grid overlay — OCR handles positioning)
    common_request = {
        "model": settings.openai_model,
        "instructions": system_prompt,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{image_base64}",
                    },
                ],
            }
        ],
        "max_output_tokens": 4096,
    }

    # Preferred path from official SDK docs: let the SDK enforce model output
    # against a Pydantic schema and return parsed data directly.
    if hasattr(client.responses, "parse"):
        response = client.responses.parse(
            **common_request,
            text_format=MenuAnalysisModel,
        )
        output_parsed = getattr(response, "output_parsed", None)
        if isinstance(output_parsed, MenuAnalysisModel):
            return output_parsed
        if isinstance(output_parsed, dict):
            return MenuAnalysisModel.model_validate(output_parsed)

    # Compatibility fallback for SDK versions without responses.parse.
    response = client.responses.create(
        **common_request,
        text={
            "format": {
                "type": "json_schema",
                "name": "menu_safety_report",
                "strict": True,
                "schema": MENU_ANALYSIS_JSON_SCHEMA,
            }
        },
    )
    raw_text = _extract_text_from_response(response)
    cleaned = _strip_markdown_fence(raw_text)
    parsed = json.loads(cleaned)
    return MenuAnalysisModel.model_validate(parsed)


def analyze_menu_image(
    image_base64: str,
    mime_type: str,
    allergies: list[str],
    medications: list[str],
    dietary_restrictions: list[str] | None = None,
) -> MenuAnalysisModel:
    # Downscale large images
    image_base64, mime_type = _downscale_image(image_base64, mime_type)

    # Step 1: Run OCR to detect text regions (precise bounding boxes)
    detect_text_regions, match_dishes_to_ocr = _lazy_ocr()
    ocr_regions = detect_text_regions(image_base64)

    # Step 2: Ask GPT to analyse the menu (safety, allergens, risk levels)
    try:
        result = _request_structured_analysis(
            image_base64=image_base64,
            mime_type=mime_type,
            allergies=allergies,
            medications=medications,
            dietary_restrictions=dietary_restrictions,
        )
    except (json.JSONDecodeError, ValueError, ValidationError):
        result = _request_structured_analysis(
            image_base64=image_base64,
            mime_type=mime_type,
            allergies=allergies,
            medications=medications,
            dietary_restrictions=dietary_restrictions,
            retry_hint=(
                "Your previous response was malformed. Return ONLY valid JSON "
                "that exactly matches the schema."
            ),
        )

    # Step 3: Merge — replace GPT's unreliable locations with OCR-detected positions
    dish_dicts = [d.model_dump() for d in result.dishes]
    match_dishes_to_ocr(dish_dicts, ocr_regions)

    # Rebuild the validated model with corrected locations
    return MenuAnalysisModel.model_validate({"dishes": dish_dicts})


def analyze_menu_image_b2b(
    image_base64: str,
    mime_type: str,
) -> MenuAnalysisModel:
    """B2B mode: comprehensive allergen extraction, no user-specific profile.
    Skips OCR since the restaurant dashboard doesn't need pin coordinates."""
    # Downscale large images
    image_base64, mime_type = _downscale_image(image_base64, mime_type)

    try:
        result = _request_structured_analysis(
            image_base64=image_base64,
            mime_type=mime_type,
            allergies=[],
            medications=[],
            system_prompt=B2B_SYSTEM_PROMPT,
            user_prompt_override=build_restaurant_prompt(),
        )
    except (json.JSONDecodeError, ValueError, ValidationError):
        result = _request_structured_analysis(
            image_base64=image_base64,
            mime_type=mime_type,
            allergies=[],
            medications=[],
            system_prompt=B2B_SYSTEM_PROMPT,
            user_prompt_override=build_restaurant_prompt(),
            retry_hint=(
                "Your previous response was malformed. Return ONLY valid JSON "
                "that exactly matches the schema."
            ),
        )

    return result
