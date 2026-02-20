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
