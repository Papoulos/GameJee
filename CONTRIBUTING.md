# Contribution workflow (GitHub conflict reduction)

If you often see conflicts in GitHub PRs, use this flow:

1. **Sync your branch before coding**
   - `git fetch origin`
   - `git rebase origin/<target-branch>` (or merge the target branch first)

2. **Keep commits narrow**
   - Prefer small, focused changes.
   - Avoid rewriting entire files when only a few lines change.

3. **Do not commit runtime state**
   - `project/memory/game_state.json` is intentionally local and ignored.
   - Keep `project/memory/game_state.template.json` as the shared baseline.

4. **Before opening a PR**
   - Rebase one more time on the latest target branch.
   - Resolve conflicts locally (simpler than GitHub UI for large files).

5. **For this repo specifically**
   - `.gitattributes` sets LF normalization and `merge=union` on:
     - `project/README.md`
     - `project/prompts/*.txt`
   - This helps reduce avoidable conflicts in documentation/prompt files.

## GitHub conflict UI: should you accept "Incoming changes"?

Short answer: **not by default**.

When GitHub shows a conflict, review each hunk and choose based on file type:

- **`project/memory/game_state.json`**: do not version runtime state. Keep it local/ignored.
- **`project/memory/game_state.template.json`**: choose the version that preserves the intended baseline, or merge both carefully.
- **Docs/prompts (`README`, `project/prompts/*.txt`)**: prefer combining both sides when both add valid content.
- **Python files**: never click "Accept incoming" blindly—merge logic manually and run checks.

If unsure, resolve locally instead of GitHub UI:

```bash
git fetch origin
git rebase origin/<target-branch>
# resolve conflicts in editor
python3 -m py_compile project/main.py project/agents/*.py project/import_content.py project/reset_memory.py
```
