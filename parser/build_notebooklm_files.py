import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/normalized/normalized_entries.json")
DEFAULT_OUTPUT_DIR = Path("data/notebooklm")
CHUNK_SIZE = 150


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build topic markdown files for NotebookLM from normalized entries."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def load_entries(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    return payload.get("entries", [])


def chunk_entries(entries: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [entries[index : index + size] for index in range(0, len(entries), size)]


def render_vocab(entry: dict[str, Any]) -> str:
    lines = [
        f"## {entry.get('jp') or 'Unknown term'}",
        f"- Meaning: {entry.get('meaning_zh') or 'Unknown'}",
    ]
    if entry.get("reading"):
        lines.append(f"- Reading: {entry['reading']}")
    if entry.get("example_jp"):
        lines.append(f"- Example: {entry['example_jp']}")
    if entry.get("source_jump_url"):
        lines.append(f"- Source: {entry['source_jump_url']}")
    return "\n".join(lines)


def render_grammar(entry: dict[str, Any]) -> str:
    lines = [
        f"## {entry.get('pattern') or 'Unknown pattern'}",
        f"- Meaning: {entry.get('meaning_zh') or 'Unknown'}",
    ]
    if entry.get("usage"):
        lines.append(f"- Usage: {entry['usage']}")
    if entry.get("example_jp"):
        lines.append(f"- Example: {entry['example_jp']}")
    if entry.get("source_jump_url"):
        lines.append(f"- Source: {entry['source_jump_url']}")
    return "\n".join(lines)


def write_kind_chunks(
    output_dir: Path, kind: str, title: str, entries: list[dict[str, Any]]
) -> int:
    chunks = chunk_entries(entries, CHUNK_SIZE)
    for index, chunk in enumerate(chunks, start=1):
        body = [f"# {title} Part {index}"]
        for entry in chunk:
            body.append("")
            if kind == "grammar":
                body.append(render_grammar(entry))
            else:
                body.append(render_vocab(entry))
        output_path = output_dir / f"{kind}_{index:02d}.md"
        output_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return len(chunks)


def main() -> None:
    args = parse_args()
    entries = load_entries(args.input)

    vocab_entries = [entry for entry in entries if entry.get("kind") == "vocab"]
    grammar_entries = [entry for entry in entries if entry.get("kind") == "grammar"]

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for old_file in args.output_dir.glob("*.md"):
        if old_file.name != ".gitkeep":
            old_file.unlink()

    file_count = 0
    if vocab_entries:
        file_count += write_kind_chunks(
            args.output_dir, "vocab", "Japanese Vocabulary Notes", vocab_entries
        )
    if grammar_entries:
        file_count += write_kind_chunks(
            args.output_dir, "grammar", "Japanese Grammar Notes", grammar_entries
        )

    print(f"Built {file_count} NotebookLM markdown files in {args.output_dir}")


if __name__ == "__main__":
    main()
