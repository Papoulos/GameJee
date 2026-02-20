from __future__ import annotations

import json
from typing import Any, Dict


class GuardAgent:
    """Validates player intent against observable context and impossibility constraints."""

    def __init__(self, llm_callable, prompt_text: str) -> None:
        self.llm = llm_callable
        self.prompt_text = prompt_text

    def review_action(self, player_action: str, observable_context: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "player_action": player_action,
            "observable_context": observable_context,
            "required_output": {
                "allowed": "bool",
                "reason": "str",
                "risk_level": "low|medium|high",
            },
        }

        raw = self.llm(self.prompt_text, json.dumps(payload, ensure_ascii=False, indent=2))
        try:
            data = json.loads(raw)
            allowed = bool(data.get("allowed", False))
            reason = str(data.get("reason", "Action rejected by Guard Agent."))
            risk_level = str(data.get("risk_level", "medium"))
            return {"allowed": allowed, "reason": reason, "risk_level": risk_level}
        except json.JSONDecodeError:
            return {
                "allowed": False,
                "reason": "Guard output was invalid. Action blocked for safety.",
                "risk_level": "high",
            }
