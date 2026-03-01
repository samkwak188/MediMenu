from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import get_settings

_LOCK = threading.RLock()
_CONNECTION: sqlite3.Connection | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get_connection() -> sqlite3.Connection:
    global _CONNECTION
    with _LOCK:
        if _CONNECTION is None:
            settings = get_settings()
            conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            _CONNECTION = conn
        return _CONNECTION


def initialize_database() -> None:
    conn = _get_connection()
    with _LOCK:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                allergies_json TEXT NOT NULL,
                medications_json TEXT NOT NULL,
                dietary_restrictions_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                dishes_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
            );
            """
        )
        # ── B2B tables ──────────────────────────────────
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurant_menus (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT NOT NULL,
                dishes_json TEXT NOT NULL,
                allergen_matrix_json TEXT NOT NULL DEFAULT '{}',
                safety_score REAL NOT NULL DEFAULT 0,
                confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_logs (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT,
                flagged_allergens_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE SET NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meal_records (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                restaurant_name TEXT NOT NULL,
                restaurant_location TEXT NOT NULL DEFAULT '',
                dish_name TEXT NOT NULL,
                ingredients_json TEXT NOT NULL DEFAULT '[]',
                date TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()


# ── User Profile CRUD ──────────────────────────────────

def create_profile(
    allergies: list[str],
    medications: list[str],
    dietary_restrictions: list[str] | None = None,
) -> dict[str, Any]:
    profile_id = str(uuid.uuid4())
    created_at = _utc_now_iso()
    conn = _get_connection()
    restrictions = dietary_restrictions or []

    with _LOCK:
        conn.execute(
            """
            INSERT INTO user_profiles (id, allergies_json, medications_json, dietary_restrictions_json, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (profile_id, json.dumps(allergies), json.dumps(medications), json.dumps(restrictions), created_at),
        )
        conn.commit()

    return {
        "id": profile_id,
        "allergies": allergies,
        "medications": medications,
        "dietary_restrictions": restrictions,
        "created_at": created_at,
    }


def get_profile(profile_id: str) -> dict[str, Any] | None:
    conn = _get_connection()
    with _LOCK:
        row = conn.execute(
            """
            SELECT id, allergies_json, medications_json, dietary_restrictions_json, created_at
            FROM user_profiles
            WHERE id = ?;
            """,
            (profile_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "allergies": json.loads(row["allergies_json"]),
        "medications": json.loads(row["medications_json"]),
        "dietary_restrictions": json.loads(row["dietary_restrictions_json"]),
        "created_at": row["created_at"],
    }


def create_analysis(profile_id: str, dishes: list[dict[str, Any]]) -> dict[str, Any]:
    analysis_id = str(uuid.uuid4())
    created_at = _utc_now_iso()
    conn = _get_connection()

    with _LOCK:
        conn.execute(
            """
            INSERT INTO analyses (id, profile_id, dishes_json, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (analysis_id, profile_id, json.dumps(dishes), created_at),
        )
        conn.commit()

    return {
        "analysis_id": analysis_id,
        "profile_id": profile_id,
        "created_at": created_at,
        "dishes": dishes,
    }


def list_history(profile_id: str, limit: int = 20) -> list[dict[str, Any]]:
    conn = _get_connection()
    with _LOCK:
        rows = conn.execute(
            """
            SELECT id, profile_id, dishes_json, created_at
            FROM analyses
            WHERE profile_id = ?
            ORDER BY created_at DESC
            LIMIT ?;
            """,
            (profile_id, limit),
        ).fetchall()

    history: list[dict[str, Any]] = []
    for row in rows:
        history.append(
            {
                "analysis_id": row["id"],
                "profile_id": row["profile_id"],
                "created_at": row["created_at"],
                "dishes": json.loads(row["dishes_json"]),
            }
        )
    return history


# ── Restaurant CRUD (B2B) ──────────────────────────────

TOP_14_ALLERGENS = [
    "milk", "eggs", "fish", "shellfish", "tree nuts",
    "peanuts", "wheat", "soybeans", "sesame", "gluten",
    "mustard", "celery", "lupin", "mollusks",
]


def create_restaurant(name: str, location: str = "") -> dict[str, Any]:
    restaurant_id = str(uuid.uuid4())
    created_at = _utc_now_iso()
    conn = _get_connection()

    with _LOCK:
        conn.execute(
            "INSERT INTO restaurants (id, name, location, created_at) VALUES (?, ?, ?, ?);",
            (restaurant_id, name, location, created_at),
        )
        conn.commit()

    return {"id": restaurant_id, "name": name, "location": location, "created_at": created_at}


def get_restaurant(restaurant_id: str) -> dict[str, Any] | None:
    conn = _get_connection()
    with _LOCK:
        row = conn.execute(
            "SELECT id, name, location, created_at FROM restaurants WHERE id = ?;",
            (restaurant_id,),
        ).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "location": row["location"], "created_at": row["created_at"]}


def list_restaurants() -> list[dict[str, Any]]:
    conn = _get_connection()
    with _LOCK:
        rows = conn.execute(
            "SELECT id, name, location, created_at FROM restaurants ORDER BY created_at DESC;"
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "location": r["location"], "created_at": r["created_at"]} for r in rows]


def _build_allergen_matrix(dishes: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build a {dish_name: {allergen: status}} matrix from analyzed dishes.

    Priority order (highest to lowest):
      1. confirmed_allergens (restaurant explicitly confirmed) → "danger"
      2. Allergen keyword found in inferred_ingredients OR AI flags → "danger"
      3. cross_contact_risk is true AND allergen is related to ingredients → "warning"
      4. No match → "safe"
    """
    # Common sub-allergen mappings for broader matching
    ALLERGEN_KEYWORDS: dict[str, list[str]] = {
        "milk": ["milk", "cheese", "butter", "cream", "yogurt", "whey", "casein", "dairy"],
        "eggs": ["egg", "eggs", "mayonnaise", "aioli"],
        "fish": ["fish", "salmon", "tuna", "cod", "tilapia", "anchovy", "anchovies"],
        "shellfish": ["shellfish", "shrimp", "crab", "lobster", "crawfish", "prawn"],
        "tree nuts": ["tree nut", "almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia"],
        "peanuts": ["peanut", "peanuts"],
        "wheat": ["wheat", "flour", "bread", "pasta", "noodle", "breaded", "batter", "tortilla"],
        "soybeans": ["soy", "soybean", "tofu", "edamame", "tempeh", "miso"],
        "sesame": ["sesame", "tahini"],
        "gluten": ["gluten", "wheat", "barley", "rye", "flour", "bread", "pasta"],
        "mustard": ["mustard"],
        "celery": ["celery"],
        "lupin": ["lupin", "lupine"],
        "mollusks": ["mollusk", "squid", "octopus", "snail", "clam", "mussel", "oyster", "scallop"],
    }

    matrix: dict[str, dict[str, str]] = {}
    for dish in dishes:
        dish_name = dish.get("dish", "Unknown")
        ingredients = " ".join(dish.get("inferred_ingredients", [])).lower()
        flags_text = " ".join(f.get("detail", "") for f in dish.get("flags", [])).lower()
        combined = f"{ingredients} {flags_text}"
        confirmed = {a.lower() for a in dish.get("confirmed_allergens", [])}
        has_cross_contact = dish.get("cross_contact_risk", False)

        row: dict[str, str] = {}
        for allergen in TOP_14_ALLERGENS:
            keywords = ALLERGEN_KEYWORDS.get(allergen, [allergen])
            keyword_found = any(kw in combined for kw in keywords)

            if allergen in confirmed:
                # 1. Restaurant explicitly confirmed this allergen
                row[allergen] = "danger"
            elif keyword_found:
                # 2. AI detected this allergen in ingredients or flags
                row[allergen] = "danger"
            elif has_cross_contact and any(kw in ingredients for kw in keywords):
                # 3. Cross-contact risk + allergen-related ingredient present
                row[allergen] = "warning"
            else:
                # 4. No evidence of this allergen
                row[allergen] = "safe"
        matrix[dish_name] = row
    return matrix


def _compute_safety_score(dishes: list[dict[str, Any]]) -> float:
    """Compute a 0–100 safety score. More OK (green) dishes = higher score.

    Each dish contributes:
      green (OK)      → 100 points
      yellow (Caution)→  50 points
      red (Avoid)     →   0 points

    Final score = average of all dish scores, minus 2 points per
    cross-contact dish (capped at 0).
    """
    if not dishes:
        return 100.0
    POINTS = {"green": 100, "yellow": 50, "red": 0}
    total = sum(POINTS.get(d.get("risk", "green"), 50) for d in dishes)
    avg = total / len(dishes)
    cross_penalty = sum(1 for d in dishes if d.get("cross_contact_risk", False)) * 2
    return max(0.0, round(avg - cross_penalty, 1))


def save_restaurant_menu(
    restaurant_id: str,
    dishes: list[dict[str, Any]],
) -> dict[str, Any]:
    menu_id = str(uuid.uuid4())
    created_at = _utc_now_iso()
    conn = _get_connection()

    allergen_matrix = _build_allergen_matrix(dishes)
    safety_score = _compute_safety_score(dishes)

    with _LOCK:
        conn.execute(
            """
            INSERT INTO restaurant_menus
                (id, restaurant_id, dishes_json, allergen_matrix_json, safety_score, confirmed, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?);
            """,
            (
                menu_id,
                restaurant_id,
                json.dumps(dishes),
                json.dumps(allergen_matrix),
                safety_score,
                created_at,
            ),
        )
        conn.commit()

    return {
        "menu_id": menu_id,
        "restaurant_id": restaurant_id,
        "dishes": dishes,
        "allergen_matrix": allergen_matrix,
        "safety_score": safety_score,
        "confirmed": False,
        "created_at": created_at,
    }


def update_restaurant_menu(
    menu_id: str,
    edited_dishes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Apply restaurant edits to a draft menu. Recalculates matrix + score."""
    conn = _get_connection()

    with _LOCK:
        row = conn.execute(
            "SELECT id, restaurant_id, dishes_json, created_at FROM restaurant_menus WHERE id = ?;",
            (menu_id,),
        ).fetchone()

    if row is None:
        return None

    # Merge edits into existing dishes
    existing_dishes: list[dict[str, Any]] = json.loads(row["dishes_json"])
    edits_by_name = {d["dish"].lower(): d for d in edited_dishes}

    for dish in existing_dishes:
        key = dish["dish"].lower()
        if key in edits_by_name:
            edit = edits_by_name[key]
            dish["inferred_ingredients"] = edit.get("inferred_ingredients", dish.get("inferred_ingredients", []))
            dish["cross_contact_risk"] = edit.get("cross_contact_risk", False)
            dish["confirmed_allergens"] = edit.get("confirmed_allergens", [])

    allergen_matrix = _build_allergen_matrix(existing_dishes)
    safety_score = _compute_safety_score(existing_dishes)

    with _LOCK:
        conn.execute(
            """
            UPDATE restaurant_menus
            SET dishes_json = ?, allergen_matrix_json = ?, safety_score = ?
            WHERE id = ?;
            """,
            (json.dumps(existing_dishes), json.dumps(allergen_matrix), safety_score, menu_id),
        )
        conn.commit()

    return {
        "menu_id": row["id"],
        "restaurant_id": row["restaurant_id"],
        "dishes": existing_dishes,
        "allergen_matrix": allergen_matrix,
        "safety_score": safety_score,
        "confirmed": False,
        "created_at": row["created_at"],
    }


def confirm_restaurant_menu(menu_id: str) -> dict[str, Any] | None:
    """Mark a menu as confirmed (reviewed by restaurant)."""
    conn = _get_connection()

    with _LOCK:
        row = conn.execute(
            """
            SELECT id, restaurant_id, dishes_json, allergen_matrix_json, safety_score, created_at
            FROM restaurant_menus WHERE id = ?;
            """,
            (menu_id,),
        ).fetchone()

        if row is None:
            return None

        conn.execute(
            "UPDATE restaurant_menus SET confirmed = 1 WHERE id = ?;",
            (menu_id,),
        )
        conn.commit()

    return {
        "menu_id": row["id"],
        "restaurant_id": row["restaurant_id"],
        "dishes": json.loads(row["dishes_json"]),
        "allergen_matrix": json.loads(row["allergen_matrix_json"]),
        "safety_score": row["safety_score"],
        "confirmed": True,
        "created_at": row["created_at"],
    }


def get_latest_menu(restaurant_id: str) -> dict[str, Any] | None:
    conn = _get_connection()
    with _LOCK:
        row = conn.execute(
            """
            SELECT id, restaurant_id, dishes_json, allergen_matrix_json, safety_score, confirmed, created_at
            FROM restaurant_menus
            WHERE restaurant_id = ?
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (restaurant_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "menu_id": row["id"],
        "restaurant_id": row["restaurant_id"],
        "dishes": json.loads(row["dishes_json"]),
        "allergen_matrix": json.loads(row["allergen_matrix_json"]),
        "safety_score": row["safety_score"],
        "confirmed": bool(row["confirmed"]),
        "created_at": row["created_at"],
    }


def get_confirmed_menu(restaurant_id: str) -> dict[str, Any] | None:
    """Get the latest *confirmed* menu for a restaurant (for consumer QR flow)."""
    conn = _get_connection()
    with _LOCK:
        row = conn.execute(
            """
            SELECT id, restaurant_id, dishes_json, allergen_matrix_json, safety_score, created_at
            FROM restaurant_menus
            WHERE restaurant_id = ? AND confirmed = 1
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (restaurant_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "menu_id": row["id"],
        "restaurant_id": row["restaurant_id"],
        "dishes": json.loads(row["dishes_json"]),
        "allergen_matrix": json.loads(row["allergen_matrix_json"]),
        "safety_score": row["safety_score"],
        "confirmed": True,
        "created_at": row["created_at"],
    }


def log_scan(restaurant_id: str | None, flagged_allergens: list[str]) -> None:
    conn = _get_connection()
    with _LOCK:
        conn.execute(
            "INSERT INTO scan_logs (id, restaurant_id, flagged_allergens_json, created_at) VALUES (?, ?, ?, ?);",
            (str(uuid.uuid4()), restaurant_id, json.dumps(flagged_allergens), _utc_now_iso()),
        )
        conn.commit()


def create_meal_record(
    profile_id: str,
    restaurant_name: str,
    restaurant_location: str,
    dish_name: str,
    ingredients: list[str],
) -> dict[str, Any]:
    record_id = str(uuid.uuid4())
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = _get_connection()

    with _LOCK:
        conn.execute(
            """
            INSERT INTO meal_records (id, profile_id, restaurant_name, restaurant_location, dish_name, ingredients_json, date)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (record_id, profile_id, restaurant_name, restaurant_location, dish_name, json.dumps(ingredients), date),
        )
        conn.commit()

    return {
        "id": record_id,
        "profile_id": profile_id,
        "restaurant_name": restaurant_name,
        "restaurant_location": restaurant_location,
        "dish_name": dish_name,
        "ingredients": ingredients,
        "date": date,
    }


def list_meal_records(profile_id: str) -> list[dict[str, Any]]:
    conn = _get_connection()
    with _LOCK:
        rows = conn.execute(
            """
            SELECT id, profile_id, restaurant_name, restaurant_location, dish_name, ingredients_json, date
            FROM meal_records
            WHERE profile_id = ?
            ORDER BY date DESC;
            """,
            (profile_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "profile_id": row["profile_id"],
            "restaurant_name": row["restaurant_name"],
            "restaurant_location": row["restaurant_location"],
            "dish_name": row["dish_name"],
            "ingredients": json.loads(row["ingredients_json"]),
            "date": row["date"],
        }
        for row in rows
    ]


def get_restaurant_analytics(restaurant_id: str) -> dict[str, Any]:
    conn = _get_connection()
    with _LOCK:
        total_scans = conn.execute(
            "SELECT COUNT(*) FROM scan_logs WHERE restaurant_id = ?;",
            (restaurant_id,),
        ).fetchone()[0]

        rows = conn.execute(
            "SELECT flagged_allergens_json FROM scan_logs WHERE restaurant_id = ?;",
            (restaurant_id,),
        ).fetchall()

    allergen_counts: dict[str, int] = {}
    for row in rows:
        for allergen in json.loads(row["flagged_allergens_json"]):
            allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1

    top_flagged = sorted(allergen_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "restaurant_id": restaurant_id,
        "total_scans": total_scans,
        "top_flagged_allergens": [{"allergen": a, "count": c} for a, c in top_flagged],
    }
