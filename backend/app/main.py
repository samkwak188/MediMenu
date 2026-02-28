from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import create_analysis, create_profile, get_profile, initialize_database, list_history
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HistoryItem,
    HistoryResponse,
    MenuAnalysisModel,
    ProfileCreateRequest,
    ProfileResponse,
)
from .services.analyzer import analyze_menu_image

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    initialize_database()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
allow_credentials = "*" not in settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/profile", response_model=ProfileResponse)
def create_profile_endpoint(payload: ProfileCreateRequest) -> ProfileResponse:
    if not payload.allergies and not payload.medications:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one allergy or one medication.",
        )

    record = create_profile(allergies=payload.allergies, medications=payload.medications)
    return ProfileResponse(**record)


@app.get("/api/profile/{profile_id}", response_model=ProfileResponse)
def get_profile_endpoint(profile_id: str) -> ProfileResponse:
    profile = get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return ProfileResponse(**profile)


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(payload: AnalyzeRequest) -> AnalyzeResponse:
    profile = get_profile(payload.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    try:
        model_output: MenuAnalysisModel = analyze_menu_image(
            image_base64=payload.image,
            mime_type=payload.mime_type,
            allergies=profile["allergies"],
            medications=profile["medications"],
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Model returned malformed JSON. Try again.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to complete analysis: {exc}",
        ) from exc

    saved = create_analysis(
        profile_id=payload.profile_id,
        dishes=[dish.model_dump() for dish in model_output.dishes],
    )
    return AnalyzeResponse(**saved)


@app.get("/api/history/{profile_id}", response_model=HistoryResponse)
def history_endpoint(profile_id: str) -> HistoryResponse:
    profile = get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    raw_history = list_history(profile_id=profile_id)
    typed_history = [HistoryItem(**item) for item in raw_history]
    return HistoryResponse(profile_id=profile_id, analyses=typed_history)
