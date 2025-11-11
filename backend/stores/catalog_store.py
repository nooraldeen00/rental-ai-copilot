from __future__ import annotations
from typing import Dict, Optional
from pathlib import Path
import csv

DEFAULT_UNIT_PRICE = 100.0

class CatalogStore:
    """
    Very small CSV-backed catalog.
    Columns expected: sku,name,unit_price
    """
    def __init__(self, csv_path: Optional[str] = None) -> None:
        # Default to data/catalog.csv at repo root
        root = Path(__file__).resolve().parents[2]  # go from backend/stores -> repo root
        self._csv_path = Path(csv_path) if csv_path else (root / "data" / "catalog.csv")
        self._by_sku: Dict[str, Dict] = {}
        self._by_name: Dict[str, Dict] = {}
        self._loaded = False

    def load(self) -> None:
        self._by_sku.clear()
        self._by_name.clear()
        if not self._csv_path.exists():
            self._loaded = True
            return
        with self._csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = (row.get("sku") or "").strip()
                name = (row.get("name") or "").strip()
                try:
                    unit_price = float(row.get("unit_price", "") or DEFAULT_UNIT_PRICE)
                except Exception:
                    unit_price = DEFAULT_UNIT_PRICE
                rec = {"sku": sku, "name": name, "unit_price": unit_price}
                if sku:
                    self._by_sku[sku.lower()] = rec
                if name:
                    self._by_name[name.lower()] = rec
        self._loaded = True

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def get_price(self, sku: Optional[str], name: Optional[str]) -> float:
        self.ensure_loaded()
        # Exact SKU match first
        if sku:
            rec = self._by_sku.get(sku.lower())
            if rec:
                return rec["unit_price"]
        # Fallback: exact name match
        if name:
            rec = self._by_name.get(name.lower())
            if rec:
                return rec["unit_price"]
        # Default
        return DEFAULT_UNIT_PRICE

CATALOG = CatalogStore()
