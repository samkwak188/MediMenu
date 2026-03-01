from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import (
    _compute_safety_score,
    confirm_restaurant_menu,
    create_analysis,
    create_profile,
    create_restaurant,
    get_confirmed_menu,
    get_latest_menu,
    get_profile,
    get_restaurant,
    get_restaurant_analytics,
    initialize_database,
    list_history,
    list_restaurants,
    log_scan,
    save_restaurant_menu,
    update_restaurant_menu,
)
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HistoryItem,
    HistoryResponse,
    MenuAnalyzeRequest,
    MenuAnalysisModel,
    MenuEditRequest,
    PersonalizedDish,
    PersonalizedMenuResponse,
    ProfileCreateRequest,
    ProfileResponse,
    RestaurantAnalyticsResponse,
    RestaurantCreateRequest,
    RestaurantMenuResponse,
    RestaurantResponse,
)
from pathlib import Path

from .services.analyzer import analyze_menu_image, analyze_menu_image_b2b

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    # Hackathon demo: start fresh every restart
    db_path = Path(settings.sqlite_path)
    if db_path.exists():
        db_path.unlink()
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


# ── B2C Endpoints ──────────────────────────────────────

@app.post("/api/profile", response_model=ProfileResponse)
def create_profile_endpoint(payload: ProfileCreateRequest) -> ProfileResponse:
    if not payload.allergies and not payload.medications and not payload.dietary_restrictions:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one allergy, medication, or dietary restriction.",
        )

    record = create_profile(
        allergies=payload.allergies,
        medications=payload.medications,
        dietary_restrictions=payload.dietary_restrictions,
    )
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
            dietary_restrictions=profile.get("dietary_restrictions", []),
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


# ── B2B Restaurant Endpoints ──────────────────────────

@app.post("/api/restaurant", response_model=RestaurantResponse)
def create_restaurant_endpoint(payload: RestaurantCreateRequest) -> RestaurantResponse:
    record = create_restaurant(name=payload.name)
    return RestaurantResponse(**record)


@app.get("/api/restaurants", response_model=list[RestaurantResponse])
def list_restaurants_endpoint() -> list[RestaurantResponse]:
    return [RestaurantResponse(**r) for r in list_restaurants()]


@app.get("/api/restaurant/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_endpoint(restaurant_id: str) -> RestaurantResponse:
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found.")
    return RestaurantResponse(**restaurant)


@app.post("/api/restaurant/{restaurant_id}/menu", response_model=RestaurantMenuResponse)
def analyze_restaurant_menu(restaurant_id: str, payload: MenuAnalyzeRequest) -> RestaurantMenuResponse:
    """Upload a menu image → AI analysis (B2B mode) → store as draft menu."""
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    try:
        model_output: MenuAnalysisModel = analyze_menu_image_b2b(
            image_base64=payload.image,
            mime_type=payload.mime_type,
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Model returned malformed JSON. Try again.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to complete analysis: {exc}") from exc

    dishes = [dish.model_dump() for dish in model_output.dishes]
    saved = save_restaurant_menu(restaurant_id=restaurant_id, dishes=dishes)
    return RestaurantMenuResponse(**saved)


@app.get("/api/restaurant/{restaurant_id}/menu", response_model=RestaurantMenuResponse)
def get_restaurant_menu(restaurant_id: str) -> RestaurantMenuResponse:
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    menu = get_latest_menu(restaurant_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="No menu uploaded yet.")
    return RestaurantMenuResponse(**menu)


@app.put("/api/restaurant/{restaurant_id}/menu", response_model=RestaurantMenuResponse)
def edit_restaurant_menu(restaurant_id: str, payload: MenuEditRequest) -> RestaurantMenuResponse:
    """Restaurant edits ingredient lists, cross-contact flags, and confirmed allergens."""
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    menu = get_latest_menu(restaurant_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="No menu to edit. Upload one first.")

    edited_dishes = [dish.model_dump() for dish in payload.dishes]
    updated = update_restaurant_menu(menu_id=menu["menu_id"], edited_dishes=edited_dishes)
    if updated is None:
        raise HTTPException(status_code=404, detail="Menu not found.")
    return RestaurantMenuResponse(**updated)


@app.post("/api/restaurant/{restaurant_id}/menu/confirm", response_model=RestaurantMenuResponse)
def confirm_menu(restaurant_id: str) -> RestaurantMenuResponse:
    """Restaurant confirms/approves the menu after review — makes it visible to consumers via QR."""
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    menu = get_latest_menu(restaurant_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="No menu to confirm.")

    confirmed = confirm_restaurant_menu(menu_id=menu["menu_id"])
    if confirmed is None:
        raise HTTPException(status_code=404, detail="Menu not found.")
    return RestaurantMenuResponse(**confirmed)


@app.get("/api/restaurant/{restaurant_id}/menu/personalized", response_model=PersonalizedMenuResponse)
def personalized_menu_endpoint(restaurant_id: str, profile_id: str) -> PersonalizedMenuResponse:
    """Consumer scans QR → get the confirmed menu re-evaluated against their profile."""
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    profile = get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    menu = get_confirmed_menu(restaurant_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="This restaurant has not published a confirmed menu yet.")

    # Re-evaluate each dish against the user's specific profile
    user_allergies = set(a.lower() for a in profile["allergies"])
    user_restrictions = set(r.lower() for r in profile.get("dietary_restrictions", []))
    flagged_allergens: list[str] = []

    personalized_dishes: list[dict] = []
    for dish in menu["dishes"]:
        ingredients_lower = [i.lower() for i in dish.get("inferred_ingredients", [])]
        ingredients_text = " ".join(ingredients_lower)
        confirmed_allergens = [a.lower() for a in dish.get("confirmed_allergens", [])]
        cross_contact = dish.get("cross_contact_risk", False)

        flags = []
        risk = "green"

        # Check allergens
        for allergen in user_allergies:
            if allergen in ingredients_text or allergen in confirmed_allergens:
                flags.append({
                    "type": "allergen",
                    "detail": f"Contains {allergen} — you listed this as an allergen",
                    "severity": "high",
                })
                risk = "red"
                flagged_allergens.append(allergen)
            elif cross_contact:
                flags.append({
                    "type": "allergen",
                    "detail": f"Possible cross-contact with {allergen} — confirm with staff",
                    "severity": "medium",
                })
                if risk != "red":
                    risk = "yellow"

        # Check dietary restrictions
        _check_dietary_restrictions(
            ingredients_text, user_restrictions, flags,
        )
        if flags and risk == "green":
            risk = "yellow"
        if any(f["severity"] == "high" for f in flags):
            risk = "red"

        personalized_dishes.append({
            "dish": dish["dish"],
            "inferred_ingredients": dish.get("inferred_ingredients", []),
            "risk": risk,
            "flags": flags,
            "safe_alternatives": dish.get("safe_alternatives"),
            "cross_contact_risk": cross_contact,
            "confirmed_allergens": dish.get("confirmed_allergens", []),
        })

    # Log the scan for analytics
    log_scan(restaurant_id, flagged_allergens)

    # Compute score from the user-personalized risk levels
    personalized_score = _compute_safety_score(personalized_dishes)

    return PersonalizedMenuResponse(
        restaurant_id=restaurant_id,
        restaurant_name=restaurant["name"],
        dishes=[PersonalizedDish(**d) for d in personalized_dishes],
        safety_score=personalized_score,
    )


def _check_dietary_restrictions(
    ingredients_text: str,
    restrictions: set[str],
    flags: list[dict],
) -> None:
    """Check dish ingredients against user dietary restrictions."""
    restriction_rules: dict[str, list[str]] = {
        "vegan": ["meat", "chicken", "beef", "pork", "fish", "shrimp", "egg", "milk",
                   "cheese", "butter", "cream", "honey", "gelatin", "lard", "bacon"],
        "vegetarian": ["meat", "chicken", "beef", "pork", "fish", "shrimp", "bacon",
                       "anchovy", "lard", "gelatin"],
        "halal": ["pork", "bacon", "lard", "alcohol", "wine", "beer", "gelatin"],
        "kosher": ["pork", "shellfish", "shrimp", "crab", "lobster", "bacon", "lard"],
        "gluten-free": ["wheat", "flour", "bread", "pasta", "noodle", "barley", "rye",
                        "crouton", "breaded", "batter"],
        "dairy-free": ["milk", "cheese", "butter", "cream", "yogurt", "whey", "casein"],
        "nut-free": ["peanut", "almond", "walnut", "cashew", "pistachio", "pecan",
                     "hazelnut", "macadamia", "tree nut"],
    }

    for restriction in restrictions:
        keywords = restriction_rules.get(restriction, [])
        for keyword in keywords:
            if keyword in ingredients_text:
                flags.append({
                    "type": "dietary_conflict",
                    "detail": f"Contains '{keyword}' — conflicts with your {restriction} restriction",
                    "severity": "high",
                })
                break  # One flag per restriction is enough


@app.get("/api/restaurant/{restaurant_id}/analytics", response_model=RestaurantAnalyticsResponse)
def restaurant_analytics_endpoint(restaurant_id: str) -> RestaurantAnalyticsResponse:
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    data = get_restaurant_analytics(restaurant_id)
    return RestaurantAnalyticsResponse(**data)
