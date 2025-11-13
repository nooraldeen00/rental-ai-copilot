# backend/core/agent_quote_planner.py
from typing import Any, Dict
from backend.core.llm import LLMClient
from backend.core.prompt import EXTRACT_SYSTEM
from backend.models import QuoteRunPayload

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_quote",
            "description": "Execute the quote with structured args",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_text": {"type": "string"},
                    "customer_tier": {"type": "string"},
                    "location": {"type": "string"},
                    "zip": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "seed": {"type": "integer"},
                },
                "required": ["request_text", "start_date", "end_date"],
            },
        },
    }
]

PLANNER_SYSTEM = """You are an orchestration agent.
Decide whether to call the tool run_quote with the given fields.
If info is sufficient, call the tool with the best-guess normalized args.
"""


def plan_and_maybe_call(payload: QuoteRunPayload) -> Dict[str, Any]:
    llm = LLMClient()
    # Give the model the normalized payload and ask it to choose the tool
    user = f"Here is the normalized payload:\n{payload.model_dump_json()}\nIf sufficient, call run_quote."
    choice = llm.tool_choice(PLANNER_SYSTEM, user, TOOLS)
    return choice  # {"name": "run_quote" or None, "arguments": {...}}
