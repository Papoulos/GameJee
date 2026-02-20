# Local Multi-Agent Game Master Prototype

A minimal Python 3.10+ tabletop RPG Game Master system using local Ollama models.

## Features

- Multi-agent architecture with strict responsibility boundaries:
  - Orchestrator (in `main.py`)
  - Narrator Agent
  - Rules Agent
  - World Authority Agent
  - Guard Agent
  - Memory Agent
- Persistent state in `memory/game_state.json`
- Data separation to prevent secret leakage
- Ollama-only LLM backend via standard library HTTP calls
- No external Python dependencies
- Ready hooks for future vector database integration
- Optional local import of rules/scenario documents from PDF/TXT/MD

## Project Layout

```text
project/
├─ main.py
├─ agents/
│  ├─ narrator.py
│  ├─ rules.py
│  ├─ world.py
│  ├─ guard.py
│  └─ memory.py
├─ prompts/
│  ├─ narrator.txt
│  ├─ rules.txt
│  ├─ world.txt
│  └─ guard.txt
├─ memory/
│  └─ game_state.json
└─ README.md
```

## Requirements

- Python 3.10+
- Ollama running locally (`http://localhost:11434`)
- A pulled model, default: `llama3.1:8b`

## Run

From the `project/` directory:

```bash
python3 main.py
```

Type actions at the prompt. Type `quit` to save and exit.

Type `reset` in-game to restore `memory/game_state.json` from `memory/game_state.template.json`.

## Import Rules or Scenario Content

You can import local files into the persistent game state:

```bash
python3 import_content.py --type rules --source /path/to/rules.pdf --title "Core Rules"
python3 import_content.py --type scenario --source /path/to/scenario.pdf --title "Chapter 1"
```

Notes:
- Supports `.pdf`, `.txt`, `.md`.
- PDF import uses local `pdftotext` (from poppler-utils).
- Imported text is cached under `memory/library/` and summarized into `game_state.json` as active references.

## How the Turn Flow Works

1. Orchestrator loads full state from Memory Agent.
2. Guard Agent checks if the action is acceptable using only observable context.
3. World Authority Agent validates plausibility and progression (can inspect hidden context).
4. Rules Agent resolves mechanics and effects as structured JSON.
5. Orchestrator applies effects and persists state.
6. Narrator Agent produces player-facing text from filtered context.

## Notes

- Only the Orchestrator sees full game state.
- Agents never write JSON directly.
- Prompts are written in English and enforce role boundaries.
- Vector DB integration points are marked in `agents/world.py` comments.
- Guard only blocks impossible/meta-gaming actions; it does not reject creative actions solely for tone.
