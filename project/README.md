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
- `memory/game_state.json` is a runtime file and can be git-ignored to prevent merge conflicts
- Data separation to prevent secret leakage
- Ollama-only LLM backend via standard library HTTP calls
- No external Python dependencies
- Ready hooks for future vector database integration
- Optional local import of rules/scenario documents from PDF/TXT/MD

## Project Layout

```text
project/
├─ main.py
├─ web_app.py
├─ web/
│  └─ index.html
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

If `memory/game_state.json` is missing, it is auto-created from `memory/game_state.template.json`.

Type actions at the prompt. Type `quit` to save and exit.

Type `reset` in-game to restore `memory/game_state.json` from `memory/game_state.template.json` (aliases accepted: `/reset`, `reinitialiser`, `réinitialiser`, `reste`).


## Web Interface

If you prefer chatting in a browser instead of CLI:

```bash
python3 web_app.py
```

Then open `http://127.0.0.1:8000`.

- Enter actions in the input box and press Enter or **Send**.
- Use **Reset Memory** to restore from `memory/game_state.template.json`.
- This web UI uses the same orchestrator and memory file as the CLI.
- The player-facing experience (CLI + web) is configured to respond in French.

If you get an error like `IndentationError` when launching `web_app.py`, your local `main.py` is likely partially merged/corrupted. Run:

```bash
python3 -m py_compile main.py
```

Then re-open `main.py` and resolve conflict markers or re-sync your branch from GitHub before retrying.

Quick re-sync (from repo root), if needed:

```bash
git fetch origin
git checkout -- project/main.py project/web_app.py project/web/index.html
git pull --rebase
```

Or use the helper script from repo root to auto-restore key files from Git HEAD:

```bash
python3 project/repair_local_files.py
```

Quick check-only mode:

```bash
python3 project/repair_local_files.py --check
```

## Import Rules or Scenario Content

You can import local files into the persistent game state:

```bash
python3 import_content.py --type rules --source /path/to/rules.pdf --title "Core Rules"
python3 import_content.py --type scenario --source /path/to/scenario.pdf --title "Chapter 1"
```

From the web UI, you can also import your own documents directly:
- choose **Règles** or **Scénario**
- provide a local file path on the machine running `web_app.py`
- optional title
- click **Importer**

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


## Git Conflict Tip

To reduce conflicts, `memory/game_state.json` is intended as local runtime state and is ignored by git. Keep `memory/game_state.template.json` as the shared baseline.

### Should I click "Accept incoming changes" on GitHub?

Usually, **no**. Use these rules:

- Runtime state (`memory/game_state.json`): do not keep it in commits.
- Shared template (`memory/game_state.template.json`): merge carefully to keep a valid baseline.
- Docs/prompts: often combine both sides instead of replacing one side.
- Python code: merge manually and run compile checks before finalizing.
