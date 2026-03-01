from __future__ import annotations

import base64
import binascii
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_IMAGE_BYTES = 20 * 1024 * 1024

DIETARY_RESTRICTION_OPTIONS = [
    "vegan",
    "vegetarian",
    "halal",
    "kosher",
    "gluten-free",
    "dairy-free",
    "nut-free",
]


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


# ── Profile Schemas ────────────────────────────────────

class ProfileCreateRequest(BaseModel):
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)

    @field_validator("allergies", "medications", mode="before")
    @classmethod
    def normalize_lists(cls, value: list[str] | str | None) -> list[str]:
        return _normalize_text_list(value)

    @field_validator("dietary_restrictions", mode="before")
    @classmethod
    def normalize_restrictions(cls, value: list[str] | str | None) -> list[str]:
        return _normalize_text_list(value)


class ProfileResponse(BaseModel):
    id: str
    allergies: list[str]
    medications: list[str]
    dietary_restrictions: list[str]
    created_at: str


# ── Analysis Schemas ───────────────────────────────────

def _validate_base64_image(value: str) -> str:
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


class AnalyzeRequest(BaseModel):
    profile_id: str = Field(min_length=1)
    image: str = Field(min_length=1)
    mime_type: str = Field(default="image/jpeg", min_length=3)

    @field_validator("image", mode="before")
    @classmethod
    def normalize_base64_image(cls, value: str) -> str:
        return _validate_base64_image(value)


class InteractionFlag(BaseModel):
    type: Literal["allergen", "medication_interaction", "dietary_conflict", "uncertainty", "other"]
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
    cross_contact_risk: bool = False
    confirmed_allergens: list[str] = Field(default_factory=list)


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


# ── B2B Restaurant Schemas ─────────────────────────────

class RestaurantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class RestaurantResponse(BaseModel):
    id: str
    name: str
    created_at: str


class MenuAnalyzeRequest(BaseModel):
    image: str = Field(min_length=1)
    mime_type: str = Field(default="image/jpeg", min_length=3)

    @field_validator("image", mode="before")
    @classmethod
    def normalize_base64_image(cls, value: str) -> str:
        return _validate_base64_image(value)


class EditedDish(BaseModel):
    """A single dish being edited by the restaurant owner."""
    dish: str = Field(min_length=1)
    inferred_ingredients: list[str] = Field(default_factory=list)
    cross_contact_risk: bool = False
    confirmed_allergens: list[str] = Field(default_factory=list)


class MenuEditRequest(BaseModel):
    """Restaurant edits a draft menu: updated ingredients, cross-contact flags."""
    dishes: list[EditedDish] = Field(min_length=1)


class AllergenFlagCount(BaseModel):
    allergen: str
    count: int


class RestaurantMenuResponse(BaseModel):
    menu_id: str
    restaurant_id: str
    dishes: list[DishResult]
    allergen_matrix: dict[str, dict[str, str]]
    safety_score: float
    confirmed: bool
    created_at: str


class PersonalizedDish(BaseModel):
    """A dish from the restaurant menu, re-evaluated for a specific user."""
    dish: str
    inferred_ingredients: list[str]
    risk: Literal["green", "yellow", "red"]
    flags: list[InteractionFlag]
    safe_alternatives: str | None = None
    cross_contact_risk: bool = False
    confirmed_allergens: list[str]


class PersonalizedMenuResponse(BaseModel):
    restaurant_id: str
    restaurant_name: str
    dishes: list[PersonalizedDish]
    safety_score: float


class RestaurantAnalyticsResponse(BaseModel):
    restaurant_id: str
    total_scans: int
    top_flagged_allergens: list[AllergenFlagCount]
