from __future__ import annotations

import json
from random import randint
from typing import Any, Dict


class RulesAgent:
    """Resolves action outcomes as structured mechanics without narration."""

    def __init__(self, llm_callable, prompt_text: str) -> None:
        self.llm = llm_callable
        self.prompt_text = prompt_text

    def evaluate_action(
        self,
        player_action: str,
        observable_context: Dict[str, Any],
        world_validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        roll = randint(1, 20)
        payload = {
            "player_action": player_action,
            "d20_roll": roll,
            "observable_context": observable_context,
            "world_validation": world_validation,
            "required_output": {
                "outcome": "success|partial_success|failure",
                "difficulty": "int",
                "mechanical_effects": {
                    "hp_delta": "int",
                    "xp_delta": "int",
                    "inventory_changes": "list[str]",
                    "new_flags": "dict[str,bool]",
                },
                "reasoning": "short rules-focused explanation",
            },
        }

        raw = self.llm(self.prompt_text, json.dumps(payload, ensure_ascii=False, indent=2))
        try:
            data = json.loads(raw)
            data.setdefault("difficulty", 12)
            data.setdefault("outcome", "failure")
            data.setdefault("mechanical_effects", {})
            effects = data["mechanical_effects"]
            effects.setdefault("hp_delta", 0)
            effects.setdefault("xp_delta", 0)
            effects.setdefault("inventory_changes", [])
            effects.setdefault("new_flags", {})
            data["d20_roll"] = roll
            return data
        except json.JSONDecodeError:
            return {
                "outcome": "failure",
                "difficulty": 12,
                "d20_roll": roll,
                "mechanical_effects": {
                    "hp_delta": 0,
                    "xp_delta": 0,
                    "inventory_changes": [],
                    "new_flags": {},
                },
                "reasoning": "Rules output was invalid JSON. Defaulting to safe failure.",
            }
