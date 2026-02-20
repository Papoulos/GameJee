from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

from agents.guard import GuardAgent
from agents.memory import MemoryAgent
from agents.narrator import NarratorAgent
from agents.rules import RulesAgent
from agents.world import WorldAuthorityAgent

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ollama_generate(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL) -> str:
    body = {
        "model": model,
        "prompt": f"{system_prompt}\n\nUSER_INPUT:\n{user_prompt}",
        "stream": False,
        "options": {"temperature": 0.4},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
        return str(parsed.get("response", "")).strip()
    except urllib.error.URLError as exc:
        return (
            "{\"error\": \"Ollama unavailable\", "
            f"\"details\": {json.dumps(str(exc))}"
            "}"
        )


class Orchestrator:
    """Coordinates all agents and controls the only full-state execution flow."""

    def __init__(self, root: Path) -> None:
        prompts_dir = root / "prompts"
        memory_path = root / "memory" / "game_state.json"

        self.memory = MemoryAgent(memory_path)
        self.guard = GuardAgent(ollama_generate, load_text(prompts_dir / "guard.txt"))
        self.rules = RulesAgent(ollama_generate, load_text(prompts_dir / "rules.txt"))
        self.world = WorldAuthorityAgent(ollama_generate, load_text(prompts_dir / "world.txt"))
        self.narrator = NarratorAgent(ollama_generate, load_text(prompts_dir / "narrator.txt"))

    def run(self) -> None:
        state = self.memory.load()
        print("Local GM prototype started. Type 'quit' to exit.")

        while True:
            observable = self.memory.get_observable_context(state)
            print("\nWhat do you do?")
            action = input("> ").strip()
            if not action:
                continue
            if action.lower() in {"quit", "exit"}:
                self.memory.save(state)
                print("Game saved. Goodbye.")
                break
            if action.lower() == "reset":
                confirmation = input("Type RESET to confirm memory reset: ").strip()
                if confirmation == "RESET":
                    template = Path(__file__).resolve().parent / "memory" / "game_state.template.json"
                    state = self.memory.reset_from_template(template)
                    print("Memory reset complete.")
                else:
                    print("Reset cancelled.")
                continue

            guard_result = self.guard.review_action(action, observable)
            if not guard_result.get("allowed", False):
                print(f"\n[Guard veto] {guard_result.get('reason', 'Action rejected.')}")
                state.setdefault("log", []).append(
                    {
                        "action": action,
                        "guard": guard_result,
                        "result": "blocked",
                    }
                )
                self.memory.save(state)
                continue

            hidden_context = state.get("hidden", {})
            scenario_context = state.get("scenario", {})
            world_result = self.world.validate_action(
                action,
                observable,
                hidden_context,
                scenario_context,
            )
            if not world_result.get("plausible", False):
                print(f"\n[World veto] {world_result.get('reason', 'Action is implausible.')}")
                state.setdefault("log", []).append(
                    {
                        "action": action,
                        "guard": guard_result,
                        "world": world_result,
                        "result": "implausible",
                    }
                )
                self.memory.save(state)
                continue

            rules_context = state.get("rules", {})
            rules_result = self.rules.evaluate_action(
                action,
                observable,
                world_result,
                rules_context,
            )
            self._apply_effects(state, rules_result, world_result)
            state.setdefault("log", []).append(
                {
                    "action": action,
                    "guard": guard_result,
                    "world": world_result,
                    "rules": rules_result,
                    "result": "resolved",
                }
            )
            self.memory.save(state)

            fresh_observable = self.memory.get_observable_context(state)
            narration = self.narrator.narrate_turn(
                fresh_observable,
                action,
                guard_result,
                rules_result,
            )
            print(f"\n{narration}")

    def _apply_effects(
        self,
        state: Dict[str, Any],
        rules_result: Dict[str, Any],
        world_result: Dict[str, Any],
    ) -> None:
        character = state.setdefault("character", {})
        flags = state.setdefault("flags", {})
        world = state.setdefault("world", {})

        effects = rules_result.get("mechanical_effects", {})
        hp_delta = int(effects.get("hp_delta", 0))
        xp_delta = int(effects.get("xp_delta", 0))
        character["hp"] = max(0, min(character.get("max_hp", 0), character.get("hp", 0) + hp_delta))
        character["xp"] = max(0, character.get("xp", 0) + xp_delta)

        for item in effects.get("inventory_changes", []):
            if isinstance(item, str) and item.startswith("+"):
                character.setdefault("inventory", []).append(item[1:].strip())
            elif isinstance(item, str) and item.startswith("-"):
                item_name = item[1:].strip()
                if item_name in character.setdefault("inventory", []):
                    character["inventory"].remove(item_name)

        for key, value in effects.get("new_flags", {}).items():
            flags[key] = bool(value)

        world_effects = world_result.get("world_effects", {})
        if world_effects.get("location_change"):
            world["current_location"] = world_effects["location_change"]

        for key, value in world_effects.get("flag_updates", {}).items():
            flags[key] = bool(value)


if __name__ == "__main__":
    Orchestrator(Path(__file__).resolve().parent).run()
