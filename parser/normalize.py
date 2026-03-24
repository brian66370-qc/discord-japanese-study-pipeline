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
EXAMPLE_RE = re.compile(r"^(?:例文|例句|例|用例|example)\s*[:：]?\s*(.+)$", re.IGNORECASE)
READING_INLINE_RE = re.compile(r"^(?P<term>.+?)[（(](?P<reading>[^)）]+)[)）]$")
READING_LABEL_RE = re.compile(r"^(?:読み|よみ|讀音|读音|reading)\s*[:：]?\s*(.+)$", re.IGNORECASE)
MEANING_LABEL_RE = re.compile(r"^(?:意味|意思|解釋|解释|meaning)\s*[:：]?\s*(.+)$", re.IGNORECASE)
GRAMMAR_LABEL_RE = re.compile(r"^(?:文法|grammar)\s*[:：]?\s*(.+)$", re.IGNORECASE)
WORD_LABEL_RE = re.compile(r"^(?:單字|单字|単語|词汇|詞彙|vocab|word)\s*[:：]?\s*(.+)$", re.IGNORECASE)
USAGE_LABEL_RE = re.compile(r"^(?:接續|接続|接续|用法|usage)\s*[:：]?\s*(.+)$", re.IGNORECASE)
NUMBERED_LINE_RE = re.compile(r"^[0-9０-９]+[\.．、]\s*(.+)$")
LEADING_MARK_RE = re.compile(r"^[・•●▪◦]\s*")
CORRECTION_RE = re.compile(r"[→⇒]")
GRAMMAR_PATTERN_RE = re.compile(r"(?:^|[\s　])(?:〜|~).+")

NOISE_PREFIXES = ("http://", "https://", "discord.com/oauth2/authorize")
SKIP_EXACT_TEXT = {
    "勉強になります🫡",
    "ﾒﾓﾒﾓ φ(´・ω・｀)なるほどなるほど、、！！",
}
GRAMMAR_USAGE_HINTS = ("接續", "接続", "接续", "辞書形", "辞書型", "ない形", "活用", "文型")


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


def parse_line_pair(line: str) -> tuple[str | None, str | None]:
    if "：" in line:
        left, right = line.split("：", 1)
        return left.strip() or None, right.strip() or None
    if ":" in line:
        left, right = line.split(":", 1)
        return left.strip() or None, right.strip() or None
    return None, None


def looks_like_example(line: str) -> bool:
    return bool(EXAMPLE_RE.match(line))


def extract_example(line: str) -> str:
    match = EXAMPLE_RE.match(line)
    return match.group(1).strip() if match else line.strip()


def normalize_bullets(line: str) -> str:
    return LEADING_MARK_RE.sub("", line).strip()


def extract_reading_from_term(term: str) -> tuple[str, str | None]:
    match = READING_INLINE_RE.match(term)
    if not match:
        return term.strip(), None
    reading = match.group("reading").strip()
    for prefix in ("読み", "よみ", "讀音", "读音"):
        if reading.startswith(prefix):
            reading = reading.replace(prefix, "", 1).strip()
            break
    return match.group("term").strip(), reading or None


def strip_known_label(line: str) -> str:
    for pattern in (WORD_LABEL_RE, GRAMMAR_LABEL_RE):
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return line.strip()


def looks_like_grammar(lines: list[str], raw_text: str) -> bool:
    if not lines:
        return False

    first = lines[0]
    if GRAMMAR_LABEL_RE.match(first):
        return True

    if any(USAGE_LABEL_RE.match(line) for line in lines[1:]):
        return True

    if any(MEANING_LABEL_RE.match(line) for line in lines[1:]) and GRAMMAR_PATTERN_RE.search(first):
        return True

    if GRAMMAR_PATTERN_RE.search(first) and any(hint in raw_text for hint in GRAMMAR_USAGE_HINTS):
        return True

    return False


def extract_vocab(lines: list[str]) -> dict[str, Any]:
    if len(lines) == 1:
        line = strip_known_label(lines[0])
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

    term_line = strip_known_label(lines[0])
    jp, reading = extract_reading_from_term(term_line)
    meaning_lines: list[str] = []
    example_lines: list[str] = []

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
        if bullet_line != line:
            example_lines.append(bullet_line)
            continue

        meaning_lines.append(line)

    return {
        "jp": jp or term_line,
        "reading": reading,
        "meaning_zh": " / ".join(meaning_lines) if meaning_lines else None,
        "example_jp": " / ".join(example_lines) if example_lines else None,
    }


def extract_grammar(lines: list[str]) -> dict[str, Any]:
    first = lines[0]
    pattern_match = GRAMMAR_LABEL_RE.match(first)
    if pattern_match:
        pattern = pattern_match.group(1).strip()
    else:
        left, right = parse_line_pair(first)
        if left and right and GRAMMAR_PATTERN_RE.search(left):
            pattern = left
            lines = [first, f"意味：{right}", *lines[1:]]
        else:
            pattern = strip_known_label(first)

    meaning_lines: list[str] = []
    example_lines: list[str] = []
    usage_lines: list[str] = []

    for line in lines[1:]:
        meaning_match = MEANING_LABEL_RE.match(line)
        if meaning_match:
            meaning_lines.append(meaning_match.group(1).strip())
            continue

        usage_match = USAGE_LABEL_RE.match(line)
        if usage_match:
            usage_lines.append(usage_match.group(1).strip())
            continue

        if looks_like_example(line):
            example_lines.append(extract_example(line))
            continue

        bullet_line = normalize_bullets(line)
        if bullet_line != line:
            if any(hint in bullet_line for hint in GRAMMAR_USAGE_HINTS):
                usage_lines.append(bullet_line)
            else:
                example_lines.append(bullet_line)
            continue

        if any(hint in line for hint in GRAMMAR_USAGE_HINTS):
            usage_lines.append(line)
            continue

        meaning_lines.append(line)

    return {
        "pattern": pattern,
        "meaning_zh": " / ".join(meaning_lines) if meaning_lines else None,
        "usage": " / ".join(usage_lines) if usage_lines else None,
        "example_jp": " / ".join(example_lines) if example_lines else None,
    }


def detect_kind(lines: list[str], raw_text: str) -> str:
    if looks_like_grammar(lines, raw_text):
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
        entry.update(extract_grammar(lines))
    else:
        entry.update(extract_vocab(lines))

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
