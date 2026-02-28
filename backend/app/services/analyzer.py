from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from ..config import get_settings
from ..prompts import MENU_ANALYSIS_JSON_SCHEMA, SYSTEM_PROMPT, build_user_prompt
from ..schemas import MenuAnalysisModel
from .text_finder import detect_text_regions, match_dishes_to_ocr

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
    retry_hint: str | None = None,
) -> MenuAnalysisModel:
    settings = get_settings()
    client = _get_client()
    user_prompt = build_user_prompt(allergies=allergies, medications=medications)
    if retry_hint:
        user_prompt = f"{user_prompt}\n\n{retry_hint}"

    # Send the ORIGINAL image to GPT (no grid overlay — OCR handles positioning)
    common_request = {
        "model": settings.openai_model,
        "instructions": SYSTEM_PROMPT,
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
) -> MenuAnalysisModel:
    # Step 1: Run OCR to detect text regions (precise bounding boxes)
    ocr_regions = detect_text_regions(image_base64)

    # Step 2: Ask GPT to analyse the menu (safety, allergens, risk levels)
    try:
        result = _request_structured_analysis(
            image_base64=image_base64,
            mime_type=mime_type,
            allergies=allergies,
            medications=medications,
        )
    except (json.JSONDecodeError, ValueError, ValidationError):
        result = _request_structured_analysis(
            image_base64=image_base64,
            mime_type=mime_type,
            allergies=allergies,
            medications=medications,
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
