from __future__ import annotations

import base64
import binascii
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_IMAGE_BYTES = 20 * 1024 * 1024


def _normalize_text_list(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []

    chunks: list[str] = []
    if isinstance(value, str):
        chunks = re.split(r"[,\n;]+", value)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                chunks.extend(re.split(r"[,\n;]+", item))

    cleaned: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        normalized = chunk.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)
    return cleaned


class ProfileCreateRequest(BaseModel):
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)

    @field_validator("allergies", "medications", mode="before")
    @classmethod
    def normalize_lists(cls, value: list[str] | str | None) -> list[str]:
        return _normalize_text_list(value)


class ProfileResponse(BaseModel):
    id: str
    allergies: list[str]
    medications: list[str]
    created_at: str


class AnalyzeRequest(BaseModel):
    profile_id: str = Field(min_length=1)
    image: str = Field(min_length=1)
    mime_type: str = Field(default="image/jpeg", min_length=3)

    @field_validator("image", mode="before")
    @classmethod
    def normalize_base64_image(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Image must be a base64 string.")

        raw = value.strip()
        if raw.startswith("data:"):
            split_value = raw.split(",", 1)
            if len(split_value) != 2:
                raise ValueError("Invalid data URL format.")
            raw = split_value[1].strip()

        try:
            decoded = base64.b64decode(raw, validate=True)
        except binascii.Error as exc:
            raise ValueError("Image is not valid base64 data.") from exc

        if len(decoded) > MAX_IMAGE_BYTES:
            raise ValueError("Image exceeds 20MB decoded size limit.")

        return raw


class InteractionFlag(BaseModel):
    type: Literal["allergen", "medication_interaction", "uncertainty", "other"]
    detail: str = Field(min_length=3)
    severity: Literal["low", "medium", "high"]


class DishLocation(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(ge=0.0, le=1.0)
    height: float = Field(ge=0.0, le=1.0)


class DishResult(BaseModel):
    dish: str = Field(min_length=1)
    inferred_ingredients: list[str] = Field(default_factory=list)
    risk: Literal["green", "yellow", "red"]
    flags: list[InteractionFlag] = Field(default_factory=list)
    safe_alternatives: str | None = None
    location: DishLocation | None = None


class MenuAnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dishes: list[DishResult] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    analysis_id: str
    profile_id: str
    created_at: str
    dishes: list[DishResult]


class HistoryItem(BaseModel):
    analysis_id: str
    profile_id: str
    created_at: str
    dishes: list[DishResult]


class HistoryResponse(BaseModel):
    profile_id: str
    analyses: list[HistoryItem]
