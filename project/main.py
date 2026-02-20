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
RESET_ALIASES = {"reset", "/reset", "réinitialiser", "reinitialiser", "reste"}


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
            "{\"error\": \"Ollama indisponible\", "
            f"\"details\": {json.dumps(str(exc))}"
            "}"
        )


class Orchestrator:
    """Coordinates all agents and controls the only full-state execution flow."""

    def __init__(self, root: Path) -> None:
        prompts_dir = root / "prompts"
        memory_path = root / "memory" / "game_state.json"

        self.root = root
        self.memory = MemoryAgent(memory_path)
        self.template_path = root / "memory" / "game_state.template.json"
        self.guard = GuardAgent(ollama_generate, load_text(prompts_dir / "guard.txt"))
        self.rules = RulesAgent(ollama_generate, load_text(prompts_dir / "rules.txt"))
        self.world = WorldAuthorityAgent(ollama_generate, load_text(prompts_dir / "world.txt"))
        self.narrator = NarratorAgent(ollama_generate, load_text(prompts_dir / "narrator.txt"))

    def _action_is_reset(self, action: str) -> bool:
        return action.casefold() in RESET_ALIASES

    def handle_action(self, action: str, confirm_reset: bool = False) -> Dict[str, Any]:
        """Process one player action and persist changes. Returns UI-ready JSON-like data."""
        state = self.memory.load()
        trimmed = action.strip()
        if not trimmed:
            return {"status": "empty", "message": "Veuillez saisir une action."}

        if self._action_is_reset(trimmed):
            if not confirm_reset:
                return {
                    "status": "reset_confirmation_required",
                    "message": "Tapez RESET pour confirmer la réinitialisation de la mémoire.",
                }
            state = self.memory.reset_from_template(self.template_path)
            return {
                "status": "reset_done",
                "message": "Réinitialisation de la mémoire terminée.",
                "observable": self.memory.get_observable_context(state),
            }

        observable = self.memory.get_observable_context(state)
        guard_result = self.guard.review_action(trimmed, observable)
        if not guard_result.get("allowed", False):
            state.setdefault("log", []).append(
                {
                    "action": trimmed,
                    "guard": guard_result,
                    "result": "blocked",
                }
            )
            self.memory.save(state)
            return {
                "status": "guard_veto",
                "message": guard_result.get("reason", "Action refusée."),
                "guard": guard_result,
                "observable": observable,
            }

        hidden_context = state.get("hidden", {})
        scenario_context = state.get("scenario", {})
        world_result = self.world.validate_action(
            trimmed,
            observable,
            hidden_context,
            scenario_context,
        )
        if not world_result.get("plausible", False):
            state.setdefault("log", []).append(
                {
                    "action": trimmed,
                    "guard": guard_result,
                    "world": world_result,
                    "result": "implausible",
                }
            )
            self.memory.save(state)
            return {
                "status": "world_veto",
                "message": world_result.get("reason", "Action invraisemblable."),
                "guard": guard_result,
                "world": world_result,
                "observable": observable,
            }

        rules_context = state.get("rules", {})
        rules_result = self.rules.evaluate_action(
            trimmed,
            observable,
            world_result,
            rules_context,
        )
        self._apply_effects(state, rules_result, world_result)
        state.setdefault("log", []).append(
            {
                "action": trimmed,
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
            trimmed,
            guard_result,
            rules_result,
        )
        return {
            "status": "resolved",
            "message": narration,
            "guard": guard_result,
            "world": world_result,
            "rules": rules_result,
            "observable": fresh_observable,
        }

    def run(self) -> None:
        print("Prototype GM local démarré. Tapez 'quit' pour quitter.")

        while True:
            print("\nQue faites-vous ?")
            action = input("> ").strip()
            if not action:
                continue
            if action.lower() in {"quit", "exit"}:
                state = self.memory.load()
                self.memory.save(state)
                print("Partie sauvegardée. Au revoir.")
                break

            if self._action_is_reset(action):
                confirmation = input("Tapez RESET pour confirmer la réinitialisation : ").strip()
                result = self.handle_action(action, confirm_reset=confirmation.upper() == "RESET")
                print(result.get("message", ""))
                continue

            result = self.handle_action(action)
            status = result.get("status")
            if status == "guard_veto":
                print(f"\n[Veto Garde] {result.get('message', 'Action refusée.')}")
            elif status == "world_veto":
                print(f"\n[Veto Monde] {result.get('message', 'Action invraisemblable.')}")
            elif status == "resolved":
                print(f"\n{result.get('message', '')}")
            else:
                print(result.get("message", "Aucune sortie."))

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
