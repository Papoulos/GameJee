from __future__ import annotations

import json
from typing import Any, Dict


class WorldAuthorityAgent:
    """Validates world plausibility and secret-safe scenario progression."""

    def __init__(self, llm_callable, prompt_text: str) -> None:
        self.llm = llm_callable
        self.prompt_text = prompt_text

    def validate_action(
        self,
        player_action: str,
        observable_context: Dict[str, Any],
        hidden_world_context: Dict[str, Any],
        scenario_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = {
            "player_action": player_action,
            "observable_context": observable_context,
            "hidden_world_context": hidden_world_context,
            "scenario_context": scenario_context,
            # Future integration: query World & Lore Vector DB here.
            # Future integration: query Scenario & Secrets Vector DB here.
            "required_output": {
                "plausible": "bool",
                "reason": "str",
                "world_effects": {
                    "location_change": "str|null",
                    "npc_updates": "list[dict]",
                    "flag_updates": "dict[str,bool]",
                },
            },
        }

        raw = self.llm(self.prompt_text, json.dumps(payload, ensure_ascii=False, indent=2))
        try:
            data = json.loads(raw)
            data.setdefault("plausible", False)
            data.setdefault("reason", "No reason provided.")
            data.setdefault("world_effects", {})
            effects = data["world_effects"]
            effects.setdefault("location_change", None)
            effects.setdefault("npc_updates", [])
            effects.setdefault("flag_updates", {})
            return data
        except json.JSONDecodeError:
            return {
                "plausible": False,
                "reason": "World validation output was invalid JSON.",
                "world_effects": {
                    "location_change": None,
                    "npc_updates": [],
                    "flag_updates": {},
                },
            }
