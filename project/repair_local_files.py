from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

FILES_TO_RESTORE = [
    "project/main.py",
    "project/web_app.py",
    "project/web/index.html",
]


def run(command: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore key project files from current Git HEAD to fix local merge corruption."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check syntax of project/main.py without restoring files.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    project_main = repo_root / "project" / "main.py"

    if args.check:
        code, output = run([sys.executable, "-m", "py_compile", str(project_main)], repo_root)
        if code == 0:
            print("main.py syntax is valid.")
            return 0
        print("main.py has syntax/indentation errors:")
        print(output)
        return 1

    code, output = run(["git", "rev-parse", "--is-inside-work-tree"], repo_root)
    if code != 0 or output.strip() != "true":
        print("This script must be run inside a Git repository clone.")
        return 1

    restore_cmd = ["git", "restore", "--source", "HEAD", "--"] + FILES_TO_RESTORE
    code, output = run(restore_cmd, repo_root)
    if code != 0:
        print("Failed to restore files from HEAD.")
        print(output)
        return 1

    print("Restored files from HEAD:")
    for path in FILES_TO_RESTORE:
        print(f"- {path}")

    code, output = run([sys.executable, "-m", "py_compile", str(project_main)], repo_root)
    if code != 0:
        print("Restored files, but main.py still fails syntax check:")
        print(output)
        return 1

    print("main.py syntax check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
