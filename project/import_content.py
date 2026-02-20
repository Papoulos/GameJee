from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict


def _extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text using local `pdftotext` command.
    Keeps project dependency-free (standard library only).
    """
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-nopgbrk", str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pdftotext is not installed. Install poppler-utils to import PDFs."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"pdftotext failed: {exc.stderr.strip()}") from exc


def _extract_text(source_path: Path) -> str:
    suffix = source_path.suffix.lower()
    if suffix == ".pdf":
        return _extract_text_from_pdf(source_path)
    if suffix in {".txt", ".md"}:
        return source_path.read_text(encoding="utf-8").strip()
    raise ValueError("Unsupported source format. Use .pdf, .txt, or .md")


def _build_summary(text: str, max_lines: int = 20) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[:max_lines]


def import_content(project_root: Path, source: Path, content_type: str, title: str | None = None) -> Path:
    memory_dir = project_root / "memory"
    state_path = memory_dir / "game_state.json"
    library_dir = memory_dir / "library" / content_type
    library_dir.mkdir(parents=True, exist_ok=True)

    if not state_path.exists():
        raise FileNotFoundError(f"Game state not found: {state_path}")

    text = _extract_text(source)
    if not text:
        raise RuntimeError("Extracted content is empty.")

    doc_name = source.stem
    target_txt = library_dir / f"{doc_name}.txt"
    target_txt.write_text(text, encoding="utf-8")

    state: Dict[str, Any] = json.loads(state_path.read_text(encoding="utf-8"))
    key = "rules" if content_type == "rules" else "scenario"
    section = state.setdefault(key, {})
    section["source_documents"] = section.get("source_documents", [])
    section["source_documents"].append(
        {
            "title": title or doc_name,
            "source": str(source),
            "cached_text": str(target_txt),
        }
    )
    section["active_summary"] = _build_summary(text)

    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return target_txt


def main() -> None:
    parser = argparse.ArgumentParser(description="Import rules or scenario content into game state.")
    parser.add_argument("--type", choices=["rules", "scenario"], required=True)
    parser.add_argument("--source", required=True, help="Path to .pdf/.txt/.md file")
    parser.add_argument("--title", required=False, help="Optional human-readable document title")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    out = import_content(project_root, source, args.type, args.title)
    print(f"Imported {args.type} content into: {out}")


if __name__ == "__main__":
    main()
