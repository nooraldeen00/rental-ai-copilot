from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from backend.db.connect import SessionLocal
import json
from typing import Any, List, Dict

router = APIRouter(prefix="/runs", tags=["runs"])

SAFE_KINDS = ("feedback_apply", "policy_guardrails")  # still useful for Python-side checks


def _to_json(obj: Any) -> Any:
    """Coerce DB value to JSON safely."""
    if obj is None:
        return {}
    if isinstance(obj, (dict, list)):
        return obj
    if isinstance(obj, (bytes, bytearray)):
        obj = obj.decode("utf-8", errors="ignore")
    if isinstance(obj, str):
        obj = obj.strip()
        if obj and obj[0] in "'{" and "'" in obj and '"' not in obj:
            try:
                obj = obj.replace("'", '"')
            except Exception:
                pass
        try:
            return json.loads(obj)
        except Exception:
            return {}
    return {}


@router.get("/{run_id}")
def get_run(run_id: int):
    with SessionLocal() as s:
        # 1) fetch full trace (ordered)
        steps = (
            s.execute(
                text(
                    """
                    SELECT id, kind, output_json
                    FROM steps
                    WHERE run_id = :rid
                    ORDER BY id ASC
                    """
                ),
                {"rid": run_id},
            )
            .mappings()
            .all()
        )

        if not steps:
            raise HTTPException(status_code=404, detail="No steps for run")

        # 2) fetch latest "quote-like" payload
        latest_row = (
            s.execute(
                text(
                    """
                    SELECT output_json
                    FROM steps
                    WHERE run_id = :rid
                      AND kind IN ('policy_guardrails', 'feedback_apply')
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ),
                {"rid": run_id},
            )
            .mappings()
            .first()
        )

        latest_json = _to_json(latest_row["output_json"]) if latest_row else {}

        # 3) serialize trace
        trace: List[Dict[str, Any]] = []
        for st in steps:
            trace.append(
                {
                    "id": st["id"],
                    "kind": st["kind"],
                    "output": _to_json(st["output_json"]),
                }
            )

        return {"quote": latest_json, "trace": trace}
