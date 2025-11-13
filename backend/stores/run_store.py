from __future__ import annotations
from typing import Dict, Any
from dataclasses import dataclass, field
import itertools
import time


@dataclass
class Run:
    id: int
    created_at: float
    input: Dict[str, Any]
    steps: list = field(default_factory=list)  # list of {"kind": str, "payload": any}
    latest_quote: Dict[str, Any] | None = None


class RunStore:
    def __init__(self) -> None:
        self._runs: Dict[int, Run] = {}
        self._ids = itertools.count(1)

    def create(self, payload: Dict[str, Any]) -> Run:
        rid = next(self._ids)
        run = Run(id=rid, created_at=time.time(), input=payload, steps=[])
        self._runs[rid] = run
        return run

    def get(self, run_id: int) -> Run | None:
        return self._runs.get(run_id)

    def update(self, run: Run) -> None:
        self._runs[run.id] = run


STORE = RunStore()
