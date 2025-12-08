# backend/routes/inventory.py
"""
Inventory browsing endpoint for RentalAI Copilot.
Provides a read-only view of available equipment categories and items.
"""
import json
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.db.connect import SessionLocal
from backend.core.logging_config import get_logger
from backend.core.exceptions import DatabaseError

router = APIRouter(prefix="/inventory", tags=["inventory"])
logger = get_logger(__name__)


# Category display names and descriptions for the UI
CATEGORY_INFO = {
    "event": {
        "name": "Event & Party",
        "description": "Tables, chairs, tents, linens, and staging for any occasion",
        "icon": "🎪",
    },
    "av": {
        "name": "Audio/Visual",
        "description": "Sound systems, microphones, projectors, and lighting",
        "icon": "🎤",
    },
    "construction": {
        "name": "Construction",
        "description": "Lifts, generators, compressors, and scaffolding",
        "icon": "🏗️",
    },
    "heavy": {
        "name": "Heavy Equipment",
        "description": "Forklifts, skid steers, and excavators",
        "icon": "🚜",
    },
    "climate": {
        "name": "Climate Control",
        "description": "Heaters, fans, and cooling equipment",
        "icon": "❄️",
    },
}


@router.get("/browse")
def browse_inventory(request: Request) -> Dict[str, Any]:
    """
    Get inventory grouped by category with pricing information.
    Returns categories with their items for the inventory browser UI.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "Fetching inventory for browse",
        extra={"extra_fields": {"request_id": request_id}},
    )

    try:
        with SessionLocal() as session:
            # Query inventory joined with rates to get pricing
            rows = (
                session.execute(
                    text(
                        """
                    SELECT
                        i.sku,
                        i.name,
                        i.location,
                        i.on_hand,
                        i.committed,
                        i.attributes,
                        r.daily,
                        r.weekly,
                        r.monthly
                    FROM inventory i
                    LEFT JOIN rates r ON i.sku = r.sku
                    ORDER BY i.name
                """
                    )
                )
                .mappings()
                .all()
            )

            # Group items by category
            categories: Dict[str, List[Dict[str, Any]]] = {}

            for row in rows:
                # Parse attributes JSON to get category
                attrs = row["attributes"]
                if isinstance(attrs, str):
                    attrs = json.loads(attrs)

                category = attrs.get("category", "other") if attrs else "other"

                # Build item object
                item = {
                    "sku": row["sku"],
                    "name": row["name"],
                    "location": row["location"],
                    "available": (row["on_hand"] or 0) - (row["committed"] or 0),
                    "dailyRate": float(row["daily"]) if row["daily"] else 0,
                    "weeklyRate": float(row["weekly"]) if row["weekly"] else 0,
                    "monthlyRate": float(row["monthly"]) if row["monthly"] else 0,
                    "attributes": attrs,
                }

                if category not in categories:
                    categories[category] = []
                categories[category].append(item)

            # Build response with category metadata
            result = []
            for cat_key, items in categories.items():
                cat_info = CATEGORY_INFO.get(
                    cat_key,
                    {
                        "name": cat_key.title(),
                        "description": f"{cat_key.title()} equipment",
                        "icon": "📦",
                    },
                )
                result.append(
                    {
                        "key": cat_key,
                        "name": cat_info["name"],
                        "description": cat_info["description"],
                        "icon": cat_info["icon"],
                        "itemCount": len(items),
                        "items": items,
                    }
                )

            # Sort categories by name
            result.sort(key=lambda x: x["name"])

            logger.info(
                f"Retrieved {len(rows)} inventory items in {len(result)} categories",
                extra={
                    "extra_fields": {"request_id": request_id, "item_count": len(rows)}
                },
            )

            return {"categories": result}

    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching inventory: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id}},
        )
        raise DatabaseError(
            "Failed to fetch inventory",
            details={"request_id": request_id, "error": str(e)},
        )
