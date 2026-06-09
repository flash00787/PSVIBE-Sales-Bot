#!/usr/bin/env python3
"""
Kora Daily Digest Generator
Reads daily logs and generates categorized digests.
stdlib only: os, json, sys, re, datetime
"""

import os
import sys
import re
from datetime import datetime, timezone

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
DIGESTS_DIR = os.path.join(MEMORY_DIR, "digests")

# ── Classification keywords (checked case-insensitive) ──────────────────────
# Priority order matters: first match wins

CATEGORIES = [
    ("💼 Business", {
        "keywords": [
            "PS VIBE", "Gaming Lounge", "customer", "member", "sales",
            "topup", "payment", "billing", "receipt",
        ],
        "emoji": "💼",
        "label": "Business",
    }),
    ("💡 Decisions", {
        "keywords": [
            "Boss directive", "Boss said", "decision", "rule", "protocol",
            "convention", "decided", "agreed", "directive",
        ],
        "emoji": "💡",
        "label": "Decisions",
    }),
    ("🎯 Pending", {
        "keywords": [
            "pending", "incomplete", "partial", "failed", "remaining",
            "TODO", "❌", "retry", "aborted", " NOT ",
        ],
        "emoji": "🎯",
        "label": "Pending",
    }),
    ("🛠️ Kora Upgrade", {
        "keywords": [
            "memory upgrade", "Phase", "memory system", "subagent",
            "journal", "Kora Upgrade", "Kora upgrade",
        ],
        "emoji": "🛠️",
        "label": "Kora Upgrade",
    }),
    ("🛠️ Tech", {
        "keywords": [
            "code", "script", "server", "deploy", "database", "API",
            "MySQL", "VPS", "Docker", "git", "bot", "app.py",
            "config.py", "sync", "integration", "nginx", "caddy",
            "firewall", "ssh", "backup", "cron",
        ],
        "emoji": "🛠️",
        "label": "Tech",
    }),
]

NOTES_LABEL = "📝 Notes"
NOTES_EMOJI = "📝"

# Display order for output
CATEGORY_ORDER = [
    "💼 Business",
    "🛠️ Tech",
    "🛠️ Kora Upgrade",
    "🎯 Pending",
    "💡 Decisions",
    "📝 Notes",
]


def get_today_str() -> str:
    """Return today's date as YYYY-MM-DD (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_utc_time_str() -> str:
    """Return current UTC time as HH:MM."""
    return datetime.now(timezone.utc).strftime("%H:%M")


def find_daily_logs() -> list:
    """Return sorted list of (date_str, path) for all daily log files."""
    results = []
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
    try:
        for fname in os.listdir(MEMORY_DIR):
            m = pattern.match(fname)
            if m:
                results.append((m.group(1), os.path.join(MEMORY_DIR, fname)))
    except FileNotFoundError:
        pass
    results.sort(key=lambda x: x[0])
    return results


def read_daily_log(date_str: str) -> str | None:
    """Read the daily log for a given date. Returns content or None."""
    path = os.path.join(MEMORY_DIR, f"{date_str}.md")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_sections(content: str) -> list[dict]:
    """
    Split content into sections based on ## headers.
    Returns list of {'title': str, 'body': str}.
    Skips the H1 title line (the "# YYYY-MM-DD" header area).
    """
    sections = []
    lines = content.split("\n")
    current_title = None
    current_body: list[str] = []
    in_h1 = True

    for line in lines:
        stripped = line.strip()

        # Skip H1 header and any lines before first ##
        if in_h1:
            if stripped.startswith("## "):
                in_h1 = False
                current_title = stripped[3:].strip()
                current_body = []
            continue

        if stripped.startswith("## "):
            # Save previous section
            if current_title is not None and current_body:
                body_text = "\n".join(current_body).strip()
                if body_text:  # skip empty sections
                    sections.append({
                        "title": current_title,
                        "body": body_text,
                    })
            current_title = stripped[3:].strip()
            current_body = []
        else:
            current_body.append(line)

    # Last section
    if current_title is not None and current_body:
        body_text = "\n".join(current_body).strip()
        if body_text:
            sections.append({
                "title": current_title,
                "body": body_text,
            })

    return sections


def classify_section(title: str, body: str) -> str:
    """
    Classify a section into one of the 6 categories.
    Priority: Business > Decisions > Pending > Kora Upgrade > Tech > Notes
    """
    combined = f"{title} {body}".lower()

    for cat_key, cat_info in CATEGORIES:
        for kw in cat_info["keywords"]:
            kw_lower = kw.lower()
            if len(kw.split()) >= 2:
                # Multi-word phrase: substring match
                if kw_lower in combined:
                    return cat_key
            else:
                # Single word: word-boundary match to avoid partial hits
                if re.search(r'\b' + re.escape(kw_lower) + r'\b', combined):
                    return cat_key

    return NOTES_LABEL


def clean_title(title: str) -> str:
    """
    Clean up a section title for display.
    Removes dates, status markers, and common prefixes.
    """
    title = title.strip()

    # Remove parenthetical dates like (2026-05-28) or (2026-05-28 08:45)
    title = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}(?:\s*[\d:]+)?\s*\)\s*$', '', title)
    title = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}(?:\s*[\d:]+)?\s*\)\s*', ' ', title)

    # Remove trailing status markers
    title = re.sub(r'\s*✅\s*\S+(?:\s+\S+){0,3}$', '', title)
    title = re.sub(r'\s*—\s*Partial\s+Progress$', '', title, flags=re.IGNORECASE)

    # Remove common verbose prefixes but keep meaningful part
    prefixes = [
        (r"^Kora\s+Upgrade\s*—\s*", ""),
        (r"^Phase\s+\d+→\d+\s+Integration\s*—?\s*", ""),
    ]
    for pattern, replacement in prefixes:
        title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)

    # Clean up extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()

    # Truncate if too long
    if len(title) > 70:
        title = title[:67] + "..."

    return title


def generate_digest(date_str: str) -> dict | None:
    """
    Generate digest for a given date.
    Returns dict with categories, summaries, and formatted output, or None.
    """
    content = read_daily_log(date_str)
    if content is None:
        return None

    sections = extract_sections(content)
    if not sections:
        return None

    # Classify each section
    categorized: dict[str, list[str]] = {cat: [] for cat in CATEGORY_ORDER}

    for section in sections:
        category = classify_section(section["title"], section["body"])
        summary = clean_title(section["title"])
        if summary:
            categorized[category].append(summary)

    # Build formatted output lines
    lines = [f"📅 {date_str} Daily Digest"]

    for cat_key in CATEGORY_ORDER:
        items = categorized.get(cat_key, [])
        if not items:
            continue
        # Get emoji and label
        emoji = NOTES_EMOJI
        label = "Notes"
        for ck, ci in CATEGORIES:
            if ck == cat_key:
                emoji = ci["emoji"]
                label = ci["label"]
                break
        summary_text = ", ".join(items)
        lines.append(f"├── {emoji} {label}: {summary_text}")

    utc_time = get_utc_time_str()
    lines.append("")
    lines.append(f"*Generated by Kora at {utc_time} UTC*")

    return {
        "date": date_str,
        "categorized": categorized,
        "formatted": "\n".join(lines),
        "sections_count": len(sections),
    }


def write_digest_file(date_str: str, formatted: str) -> str:
    """Write digest to memory/digests/YYYY-MM-DD-digest.md. Returns path."""
    digests_dir = DIGESTS_DIR

    def try_write(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{date_str}-digest.md")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(formatted + "\n")
            return path
        except (PermissionError, OSError):
            return None

    # Try primary dir
    path = try_write(digests_dir)
    if path:
        return path

    # Fallback to /tmp
    digests_dir = os.path.join("/tmp", "kora_digests")
    os.makedirs(digests_dir, exist_ok=True)
    path = os.path.join(digests_dir, f"{date_str}-digest.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(formatted + "\n")
    print(f"⚠️ Using fallback: {path}")
    return path


def cmd_today(send: bool = False, date_str: str | None = None):
    """Generate digest for today (or specified date)."""
    if date_str is None:
        date_str = get_today_str()

    result = generate_digest(date_str)
    if result is None:
        print(f"❌ No daily log found for {date_str}", file=sys.stderr)
        sys.exit(1)

    # Always write to file
    path = write_digest_file(date_str, result["formatted"])
    print(f"📄 Digest written: {path}")

    if send:
        print("")
        print("─── Telegram-Ready ───")
        print(result["formatted"])
        print("─── End ───")

    # Print quick summary to stdout
    print(f"\n📊 {date_str}: {result['sections_count']} sections categorized")
    for cat_key in CATEGORY_ORDER:
        items = result["categorized"].get(cat_key, [])
        if items:
            emoji = NOTES_EMOJI
            label = "Notes"
            for ck, ci in CATEGORIES:
                if ck == cat_key:
                    emoji = ci["emoji"]
                    label = ci["label"]
                    break
            print(f"   {emoji} {label}: {len(items)} items")


def cmd_all(send: bool = False):
    """Generate digests for all available dates."""
    logs = find_daily_logs()
    if not logs:
        print("❌ No daily log files found.", file=sys.stderr)
        sys.exit(1)

    generated = 0
    for date_str, _path in logs:
        result = generate_digest(date_str)
        if result is None:
            print(f"⚠️  Skipped {date_str} (empty or unreadable)")
            continue

        path = write_digest_file(date_str, result["formatted"])
        print(f"📄 {date_str} → {path}")

        if send:
            print(f"\n─── {date_str} Telegram ───")
            print(result["formatted"])
            print("─── End ───\n")

        generated += 1

    print(f"\n✅ {generated} digest(s) generated")


def print_usage():
    """Print usage information."""
    print("Usage: python3 daily_digest.py [OPTIONS]")
    print("")
    print("Options:")
    print("  --today            Generate digest for today (default)")
    print("  --date YYYY-MM-DD  Generate digest for a specific date")
    print("  --send             Also print Telegram-ready markdown")
    print("  --all              Generate digests for ALL available dates")
    print("  --help             Show this help message")
    print("")
    print("Output:")
    print("  - Writes digest to memory/digests/YYYY-MM-DD-digest.md")
    print("  - --send also prints clean markdown for Telegram")
    print("")
    print("Classification Categories (priority order):")
    print("  💼 Business    — PS VIBE, Gaming Lounge, customer, sales, payment")
    print("  💡 Decisions   — decision, rule, protocol, Boss directive")
    print("  🎯 Pending     — pending, incomplete, partial, failed, TODO, ❌")
    print("  🛠️ Kora Upgrade — memory upgrade, Phase, subagent, journal")
    print("  🛠️ Tech        — code, server, database, API, MySQL, VPS, bot")
    print("  📝 Notes       — everything else")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_usage()
        sys.exit(0)

    send = "--send" in args
    args = [a for a in args if a != "--send"]

    if "--all" in args:
        cmd_all(send=send)
        return

    # Check for --date
    date_str = None
    for i, arg in enumerate(args):
        if arg == "--date" and i + 1 < len(args):
            date_str = args[i + 1]
            # Validate date format
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                print(f"❌ Invalid date format: {date_str}. Use YYYY-MM-DD.", file=sys.stderr)
                sys.exit(1)
            break
        elif arg == "--date":
            print("❌ --date requires a value: YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    if "--today" in args or not args:
        cmd_today(send=send, date_str=date_str)
        return

    # Filter out known args
    remaining = []
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in ("--today",):
            continue
        if a == "--date":
            skip = True
            continue
        remaining.append(a)

    if remaining:
        print(f"❌ Unrecognized arguments: {' '.join(remaining)}", file=sys.stderr)
        print_usage()
        sys.exit(1)

    # Default: --today
    cmd_today(send=send)


if __name__ == "__main__":
    main()
