# backend/core/tracing.py
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Result

from backend.db.connect import SessionLocal


def _dumps(obj: Any) -> str:
    """Safe JSON serialization (falls back to repr if needed)."""
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        # last resort to avoid crashing tracing
        return json.dumps({"_nonjson": repr(obj)}, ensure_ascii=False)


def _fetch_last_inserted_id(result: Result) -> Optional[int]:
    """
    Try to get inserted id in a way that works across SQLite/MySQL/Postgres.
    - Prefer RETURNING id (Postgres/MySQL 8.0.21+ with SQLAlchemy text RETURNING).
    - Else fall back to DBAPI cursor.lastrowid (SQLite/MySQL).
    """
    try:
        # If INSERT ... RETURNING id was used:
        row = result.fetchone()
        if row and ("id" in row._mapping):
            return int(row._mapping["id"])
    except Exception:
        pass

    try:
        # Fallback to DBAPI cursor attribute (SQLite/MySQL)
        if hasattr(result, "lastrowid") and result.lastrowid:
            return int(result.lastrowid)  # type: ignore[attr-defined]
        if hasattr(result, "cursor") and getattr(result.cursor, "lastrowid", None):
            return int(result.cursor.lastrowid)  # type: ignore[attr-defined]
    except Exception:
        pass

    return None


def start_run(input_text: str, seed: Optional[int]) -> int:
    """
    Create a run row with status='running'. Returns the new run id.
    Table expected: runs(id PK, input_text TEXT, seed INT, status TEXT, cost_usd REAL, created_at ...)
    """
    with SessionLocal() as s:
        # Try RETURNING first (best for Postgres; also supported by recent MySQL)
        try:
            result = s.execute(
                text(
                    "INSERT INTO runs (input_text, seed, status, cost_usd) "
                    "VALUES (:t, :seed, 'running', 0) RETURNING id"
                ),
                {"t": input_text, "seed": seed if seed is not None else 0},
            )
            s.commit()
            rid = _fetch_last_inserted_id(result)
            if rid is not None:
                return rid
        except Exception:
            s.rollback()
            # Fallback path without RETURNING
            result = s.execute(
                text(
                    "INSERT INTO runs (input_text, seed, status, cost_usd) "
                    "VALUES (:t, :seed, 'running', 0)"
                ),
                {"t": input_text, "seed": seed if seed is not None else 0},
            )
            s.commit()
            rid = _fetch_last_inserted_id(result)
            if rid is not None:
                return rid

            # Absolute fallback for SQLite
            with SessionLocal() as s2:
                row = s2.execute(text("SELECT last_insert_rowid() AS id")).mappings().first()
                if row and "id" in row:
                    return int(row["id"])

    raise RuntimeError("Failed to create run id")


def add_step(run_id: int, kind: str, input_json: Any, output_json: Any, duration_ms: int) -> None:
    """
    Append a step to the steps table. Stores valid JSON in input_json/output_json.
    Table expected: steps(id PK, run_id INT, kind TEXT, input_json TEXT, output_json TEXT, duration_ms INT, created_at ...)
    """
    with SessionLocal() as s:
        s.execute(
            text(
                "INSERT INTO steps (run_id, kind, input_json, output_json, duration_ms) "
                "VALUES (:rid, :k, :in_json, :out_json, :dur)"
            ),
            {
                "rid": run_id,
                "k": kind,
                "in_json": _dumps(input_json),
                "out_json": _dumps(output_json),
                "dur": int(duration_ms or 0),
            },
        )
        s.commit()


def finish_run(run_id: int, cost: float = 0.0) -> None:
    """
    Mark run finished and record total cost.
    """
    with SessionLocal() as s:
        s.execute(
            text("UPDATE runs SET status='finished', cost_usd=:c WHERE id=:rid"),
            {"c": float(cost or 0.0), "rid": run_id},
        )
        s.commit()
