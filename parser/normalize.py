import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/raw/raw_messages.json")
DEFAULT_OUTPUT = Path("data/normalized/normalized_entries.json")

SEPARATOR_RE = re.compile(r"^[ー—\-_=]{5,}$")
URL_ONLY_RE = re.compile(r"^(https?://\S+)$", re.IGNORECASE)
DISCORD_EMOJI_RE = re.compile(r"^<a?:[A-Za-z0-9_]+:\d+>$")
MARKDOWN_EMOJI_LINK_RE = re.compile(r"^\[[^\]]+\]\(https?://[^\)]+\)$", re.IGNORECASE)
EXAMPLE_RE = re.compile(r"^(?:例|例文|例句|用例)\s*[:：]?\s*(.+)$")
READING_INLINE_RE = re.compile(r"^(?P<term>.+?)[（(](?P<reading>[^)）]+)[)）]$")
READING_LABEL_RE = re.compile(r"^(?:読み|よみ|reading)\s*[:：]?\s*(.+)$", re.IGNORECASE)
MEANING_LABEL_RE = re.compile(r"^(?:意味|意思|meaning)\s*[:：]?\s*(.+)$", re.IGNORECASE)
GRAMMAR_LABEL_RE = re.compile(r"^(?:文法|grammar)\s*[:：]?\s*(.+)$", re.IGNORECASE)
NUMBERED_LINE_RE = re.compile(r"^[0-9０-９]+[\.．、]\s*(.+)$")
LEADING_MARK_RE = re.compile(r"^[・•●▪◦]\s*")
CORRECTION_RE = re.compile(r"[→⇒]")

GRAMMAR_HINTS = ("〜", "~", "文法", "grammar", "接続", "接續", "活用", "辞書形", "ない形")
NOISE_PREFIXES = ("http://", "https://", "discord.com/oauth2/authorize")
SKIP_EXACT_TEXT = {
    "勉強になります🫡",
    "ﾒﾓﾒﾓ φ(´・ω・｀)なるほどなるほど、、！！",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize raw Discord messages into study entries."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_payload(input_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return json.loads(input_path.read_text(encoding="utf-8"))


def clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if SEPARATOR_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def is_noise_message(text: str) -> bool:
    if not text:
        return True
    if text in SKIP_EXACT_TEXT:
        return True
    if text.startswith(NOISE_PREFIXES):
        return True
    if URL_ONLY_RE.fullmatch(text):
        return True
    if DISCORD_EMOJI_RE.fullmatch(text):
        return True
    if MARKDOWN_EMOJI_LINK_RE.fullmatch(text):
        return True
    if re.fullmatch(r"[!！?？wW\s]+", text):
        return True
    if "<:" in text and len(text.splitlines()) == 1 and len(text) < 60:
        return True
    return False


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def looks_like_example(line: str) -> bool:
    return bool(EXAMPLE_RE.match(line))


def extract_example(line: str) -> str:
    match = EXAMPLE_RE.match(line)
    return match.group(1).strip() if match else line.strip()


def extract_reading_from_term(term: str) -> tuple[str, str | None]:
    match = READING_INLINE_RE.match(term)
    if not match:
        return term.strip(), None
    reading = match.group("reading").strip()
    if reading.startswith("読み"):
        reading = reading.replace("読み", "", 1).strip()
    return match.group("term").strip(), reading or None


def looks_like_grammar(text: str, lines: list[str]) -> bool:
    if not lines:
        return False
    first = lines[0]
    if GRAMMAR_LABEL_RE.match(first):
        return True
    if any(hint in text for hint in GRAMMAR_HINTS):
        if any(label in text for label in ("意味", "意思", "接続", "接續", "辞書形", "ない形")):
            return True
        if "〜" in first or "~" in first:
            return True
    return False


def parse_line_pair(line: str) -> tuple[str | None, str | None]:
    if "：" in line:
        left, right = line.split("：", 1)
        return left.strip() or None, right.strip() or None
    if ":" in line:
        left, right = line.split(":", 1)
        return left.strip() or None, right.strip() or None
    return None, None


def normalize_bullets(line: str) -> str:
    return LEADING_MARK_RE.sub("", line).strip()


def extract_vocab(lines: list[str], raw_text: str) -> dict[str, Any]:
    if len(lines) == 1:
        line = lines[0]
        left, right = parse_line_pair(line)
        if left and right and left not in {"例", "例文", "例句"}:
            jp, reading = extract_reading_from_term(left)
            return {
                "jp": jp or left,
                "reading": reading,
                "meaning_zh": right,
                "example_jp": None,
            }

        jp, reading = extract_reading_from_term(line)
        return {
            "jp": jp,
            "reading": reading,
            "meaning_zh": "word choice correction" if CORRECTION_RE.search(line) else None,
            "example_jp": None,
        }

    term_line = lines[0]
    meaning_lines: list[str] = []
    example_lines: list[str] = []
    reading: str | None = None

    labeled_term = GRAMMAR_LABEL_RE.match(term_line)
    if labeled_term:
        term_line = labeled_term.group(1).strip()

    jp, inline_reading = extract_reading_from_term(term_line)
    reading = inline_reading

    for line in lines[1:]:
        reading_match = READING_LABEL_RE.match(line)
        if reading_match:
            reading = reading_match.group(1).strip()
            continue

        meaning_match = MEANING_LABEL_RE.match(line)
        if meaning_match:
            meaning_lines.append(meaning_match.group(1).strip())
            continue

        if looks_like_example(line):
            example_lines.append(extract_example(line))
            continue

        if line.startswith("：") or line.startswith(":"):
            example_lines.append(line[1:].strip())
            continue

        numbered = NUMBERED_LINE_RE.match(line)
        if numbered:
            meaning_lines.append(numbered.group(1).strip())
            continue

        bullet_line = normalize_bullets(line)
        if bullet_line != line and jp not in {"", None}:
            example_lines.append(bullet_line)
            continue

        meaning_lines.append(line)

    if not reading:
        for line in lines[1:]:
            nested_term, nested_reading = extract_reading_from_term(line)
            if nested_reading and nested_term == line.split("（", 1)[0].split("(", 1)[0].strip():
                reading = nested_reading
                break

    return {
        "jp": jp or term_line,
        "reading": reading,
        "meaning_zh": " / ".join(meaning_lines) if meaning_lines else None,
        "example_jp": " / ".join(example_lines) if example_lines else None,
    }


def extract_grammar(lines: list[str], raw_text: str) -> dict[str, Any]:
    pattern: str | None = None
    meaning_lines: list[str] = []
    example_lines: list[str] = []
    usage_lines: list[str] = []

    first = lines[0]
    match = GRAMMAR_LABEL_RE.match(first)
    if match:
        pattern = match.group(1).strip()
    else:
        left, right = parse_line_pair(first)
        if left and right and ("〜" in left or "~" in left):
            pattern = left
            meaning_lines.append(right)
        else:
            pattern = first

    for line in lines[1:]:
        meaning_match = MEANING_LABEL_RE.match(line)
        if meaning_match:
            meaning_lines.append(meaning_match.group(1).strip())
            continue
        if looks_like_example(line):
            example_lines.append(extract_example(line))
            continue
        if any(key in line for key in ("接続", "接續", "辞書形", "ない形")):
            usage_lines.append(normalize_bullets(line))
            continue
        bullet_line = normalize_bullets(line)
        if bullet_line != line:
            example_lines.append(bullet_line)
            continue
        meaning_lines.append(line)

    return {
        "pattern": pattern,
        "meaning_zh": " / ".join(meaning_lines) if meaning_lines else None,
        "usage": " / ".join(usage_lines) if usage_lines else None,
        "example_jp": " / ".join(example_lines) if example_lines else None,
    }


def detect_kind(lines: list[str], raw_text: str) -> str:
    if looks_like_grammar(raw_text, lines):
        return "grammar"
    return "vocab"


def normalize_message(message: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = clean_text(message.get("content", ""))
    if not raw_text or is_noise_message(raw_text):
        return []

    lines = split_lines(raw_text)
    if not lines:
        return []

    kind = detect_kind(lines, raw_text)
    entry: dict[str, Any] = {
        "entry_id": f"msg_{message['id']}_1",
        "source_message_id": message["id"],
        "source_jump_url": message.get("jump_url"),
        "created_at": message.get("created_at"),
        "kind": kind,
        "raw_text": raw_text,
        "tags": [],
    }

    if kind == "grammar":
        entry.update(extract_grammar(lines, raw_text))
    else:
        entry.update(extract_vocab(lines, raw_text))

    return [entry]


def main() -> None:
    args = parse_args()
    payload = load_payload(args.input)

    entries: list[dict[str, Any]] = []
    skipped_count = 0
    for message in payload.get("messages", []):
        normalized = normalize_message(message)
        if normalized:
            entries.extend(normalized)
        else:
            skipped_count += 1

    output = {
        "source": {
            "guild_id": payload.get("guild_id"),
            "guild_name": payload.get("guild_name"),
            "channel_id": payload.get("channel_id"),
            "channel_name": payload.get("channel_name"),
        },
        "entry_count": len(entries),
        "skipped_message_count": skipped_count,
        "entries": entries,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Normalized {len(entries)} entries into {args.output}")
    print(f"Skipped {skipped_count} messages as empty or obvious noise")


if __name__ == "__main__":
    main()
