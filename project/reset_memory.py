from __future__ import annotations

import argparse
from pathlib import Path

from agents.memory import MemoryAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset memory/game_state.json from a template file.")
    parser.add_argument(
        "--template",
        default="memory/game_state.template.json",
        help="Template path relative to project root (default: memory/game_state.template.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reset without confirmation prompt",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    memory = MemoryAgent(root / "memory" / "game_state.json")
    template = root / args.template

    if not args.force:
        confirmation = input("This will overwrite memory/game_state.json. Type 'RESET' to continue: ").strip()
        if confirmation != "RESET":
            print("Reset cancelled.")
            return

    memory.reset_from_template(template)
    print(f"Game state reset from: {template}")


if __name__ == "__main__":
    main()
