from __future__ import annotations

import json
from typing import Any, Dict


class NarratorAgent:
    """Produces player-facing narrative from filtered context only."""

    def __init__(self, llm_callable, prompt_text: str) -> None:
        self.llm = llm_callable
        self.prompt_text = prompt_text

    def narrate_turn(
        self,
        observable_context: Dict[str, Any],
        player_action: str,
        guard_result: Dict[str, Any],
        rules_result: Dict[str, Any],
    ) -> str:
        payload = {
            "observable_context": observable_context,
            "player_action": player_action,
            "guard_result": guard_result,
            "rules_result": rules_result,
            "style_requirements": [
                "Keep it concise (2-4 short paragraphs).",
                "Do not expose hidden data.",
                "Include immediate sensory details and next possible choices.",
            ],
        }
        return self.llm(self.prompt_text, json.dumps(payload, ensure_ascii=False, indent=2)).strip()
