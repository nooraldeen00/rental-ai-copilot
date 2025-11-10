import time
from sqlalchemy import text
from backend.db.connect import SessionLocal

def start_run(input_text: str, seed: int|None):
    with SessionLocal() as s:
        res = s.execute(text(
            "INSERT INTO runs (input_text, seed, status, cost_usd) VALUES (:t,:seed,'running',0)"
        ), {"t": input_text, "seed": seed}).lastrowid
        s.commit()
        return res

def add_step(run_id: int, kind: str, input_json, output_json, latency_ms: int):
    with SessionLocal() as s:
        s.execute(text(
            "INSERT INTO steps (run_id, kind, input_json, output_json, latency_ms) VALUES (:rid,:k,:in,:out,:lat)"
        ), {"rid": run_id, "k": kind, "in": str(input_json), "out": str(output_json), "lat": latency_ms})
        s.commit()

def finish_run(run_id: int, cost: float = 0.0):
    with SessionLocal() as s:
        s.execute(text("UPDATE runs SET status='finished', cost_usd=:c WHERE id=:rid"),
                  {"c": cost, "rid": run_id})
        s.commit()
