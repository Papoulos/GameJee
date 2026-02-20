from __future__ import annotations

import json
from typing import Any, Dict


class GuardAgent:
    """Blocks only impossible or meta-gaming actions from observable context."""

    def __init__(self, llm_callable, prompt_text: str) -> None:
        self.llm = llm_callable
        self.prompt_text = prompt_text

    def review_action(self, player_action: str, observable_context: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "player_action": player_action,
            "observable_context": observable_context,
            "required_output": {
                "allowed": "bool",
                "block_category": "impossible|metagaming|none",
                "reason": "str",
                "risk_level": "low|medium|high",
            },
        }

        raw = self.llm(self.prompt_text, json.dumps(payload, ensure_ascii=False, indent=2))
        try:
            data = json.loads(raw)
            allowed = bool(data.get("allowed", True))
            block_category = str(data.get("block_category", "none"))
            reason = str(data.get("reason", "Action accepted."))
            risk_level = str(data.get("risk_level", "low"))

            # Safety valve: guard can only veto impossible or hidden-knowledge/meta actions.
            if not allowed and block_category not in {"impossible", "metagaming"}:
                return {
                    "allowed": True,
                    "block_category": "none",
                    "reason": "Guard softened veto: action is unusual but still possible.",
                    "risk_level": "low",
                }

            return {
                "allowed": allowed,
                "block_category": block_category,
                "reason": reason,
                "risk_level": risk_level,
            }
        except json.JSONDecodeError:
            # Fail open to avoid over-restriction; impossible actions are still filtered by World Agent.
            return {
                "allowed": True,
                "block_category": "none",
                "reason": "Guard output invalid JSON; defaulting to permissive mode.",
                "risk_level": "low",
            }
