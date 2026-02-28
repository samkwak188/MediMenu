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
        conn.commit()


def create_profile(allergies: list[str], medications: list[str]) -> dict[str, Any]:
    profile_id = str(uuid.uuid4())
    created_at = _utc_now_iso()
    conn = _get_connection()

    with _LOCK:
        conn.execute(
            """
            INSERT INTO user_profiles (id, allergies_json, medications_json, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (profile_id, json.dumps(allergies), json.dumps(medications), created_at),
        )
        conn.commit()

    return {
        "id": profile_id,
        "allergies": allergies,
        "medications": medications,
        "created_at": created_at,
    }


def get_profile(profile_id: str) -> dict[str, Any] | None:
    conn = _get_connection()
    with _LOCK:
        row = conn.execute(
            """
            SELECT id, allergies_json, medications_json, created_at
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
