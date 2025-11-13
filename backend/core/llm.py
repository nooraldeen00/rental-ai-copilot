# backend/core/llm.py
import os
import json
from typing import Any, Dict, Optional, List


class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        if self.provider == "openai":
            from openai import OpenAI

            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}")

    def json_chat(
        self, system: str, user: str, json_schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Ask the model to return STRICT JSON. If provider supports schema, use it.
        Fallback to parseable JSON with guardrails.
        """
        if self.provider == "openai":
            # Uses response_format="json_object" for strict JSON
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = resp.choices[0].message.content
            return json.loads(content)

        elif self.provider == "anthropic":
            # Anthropic: ask for JSON via instructions + delimiter
            msg = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.2,
                system=system + "\nReturn ONLY valid JSON with no commentary.",
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(
                [b.text for b in msg.content if getattr(b, "type", "") == "text"]
            )
            # best-effort JSON parse (could add a small fixer if needed)
            return json.loads(text)

    def tool_choice(
        self, system: str, user: str, tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simple tool calling abstraction (OpenAI-style). For Anthropic, emulate via JSON.
        For MVP we’ll keep it simple: return a dict describing which tool + args.
        """
        if self.provider == "openai":
            # Using tool definitions (function calling)
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
            )
            msg = resp.choices[0].message
            if msg.tool_calls:
                tc = msg.tool_calls[0]
                return {
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                }
            # default noop
            return {"name": None, "arguments": {}}

        # Fallback for Anthropic: ask model to return JSON {tool_name, arguments}
        prompt = (
            system + "\n"
            'Return JSON ONLY as: {"name": "<toolName or null>", "arguments": { ...validated args... }}\n'
        )
        return self.json_chat(prompt, user)
