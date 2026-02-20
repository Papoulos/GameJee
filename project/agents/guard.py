from __future__ import annotations

import json
from typing import Any, Dict


class GuardAgent:
    """Blocks meta-gaming and only clearly impossible actions from observable context."""

    _IMPOSSIBLE_KEYWORDS = {
        "teleport",
        "time travel",
        "phase through",
        "walk through wall",
        "become immortal",
        "become a god",
        "spawn item",
        "noclip",
        "fly to the moon",
    }
    """Validates player intent against observable context and tone constraints."""

    def __init__(self, llm_callable, prompt_text: str) -> None:
        self.llm = llm_callable
        self.prompt_text = prompt_text

    def _clearly_impossible(self, action: str) -> bool:
        lowered = action.casefold()
        return any(token in lowered for token in self._IMPOSSIBLE_KEYWORDS)

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

            if not allowed and block_category == "metagaming":
                return {
                    "allowed": False,
                    "block_category": block_category,
                    "reason": reason,
                    "risk_level": risk_level,
                }

            if not allowed and block_category == "impossible":
                if self._clearly_impossible(player_action):
                    return {
                        "allowed": False,
                        "block_category": block_category,
                        "reason": reason,
                        "risk_level": risk_level,
                    }
                return {
                    "allowed": True,
                    "block_category": "none",
                    "reason": "Guard softened veto: action is not clearly impossible.",
                    "risk_level": "low",
                }

            if not allowed:
                return {
                    "allowed": True,
                    "block_category": "none",
                    "reason": "Guard softened veto: action is unusual but still possible.",
                    "risk_level": "low",
                }

            return {
                "allowed": True,
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
