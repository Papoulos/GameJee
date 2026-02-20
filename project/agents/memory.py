from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict


class MemoryAgent:
    """Single source of truth for persistent game state."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            template = self.path.with_name("game_state.template.json")
            if template.exists():
                with template.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                self.save(state)
                return state
            raise FileNotFoundError(f"Game state file not found: {self.path}")
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, state: Dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def reset_from_template(self, template_path: str | Path) -> Dict[str, Any]:
        template = Path(template_path)
        if not template.exists():
            raise FileNotFoundError(f"Template state not found: {template}")
        with template.open("r", encoding="utf-8") as f:
            state = json.load(f)
        self.save(state)
        return state

    def get_observable_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return only information a player character could reasonably observe.
        Hidden scenario sections are intentionally excluded.
        """
        character = state.get("character", {})
        world = state.get("world", {})

        observable = {
            "character": {
                "name": character.get("name"),
                "class": character.get("class"),
                "level": character.get("level"),
                "hp": character.get("hp"),
                "max_hp": character.get("max_hp"),
                "stats": deepcopy(character.get("stats", {})),
                "inventory": deepcopy(character.get("inventory", [])),
                "xp": character.get("xp"),
            },
            "world": {
                "current_location": world.get("current_location"),
                "known_npcs": deepcopy(world.get("known_npcs", [])),
                "factions": deepcopy(world.get("factions", [])),
                "visible_scene": deepcopy(world.get("visible_scene", {})),
            },
            "flags": {
                k: v
                for k, v in state.get("flags", {}).items()
                if not k.startswith("secret_")
            },
            "log": deepcopy(state.get("log", [])[-8:]),
        }
        return observable
