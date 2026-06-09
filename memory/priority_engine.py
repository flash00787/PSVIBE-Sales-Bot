#!/usr/bin/env python3
"""
Priority Memory Engine — classifies memory entries by priority level
and manages storage by P0/P1/P2/P3 tiers.

Priority Levels:
  P0 (Critical) — Boss's rules, business decisions, security configs,
                   API keys, passwords → Never delete, always in MEMORY.md
  P1 (Important) — Project updates, significant events, architecture
                    decisions → 30 days in MEMORY.md, then can archive
  P2 (Normal) — Task completions, routine info, daily notes
                 → 7 days in daily logs
  P3 (Transient) — One-time conversations, temp info, debug output
                    → 24h then prune

Usage:
  python3 priority_engine.py                       # Quick status summary
  python3 priority_engine.py --classify "<text>"   # Test classify text
  python3 priority_engine.py --audit               # Scan MEMORY.md + daily logs
  python3 priority_engine.py --audit-file <path>   # Classify entries in a file
"""

import os
import sys
import re
import json
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parent.parent  # /root/.openclaw/workspace
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_MD = WORKSPACE / "MEMORY.md"

# ── Keyword Rules ──────────────────────────────────────────────────────────
# Matched case-insensitively against full entry text.
# Priority chain: first P0 hit wins; then P1; then P2; then P3; else default P2.

P0_KEYWORDS = [
    r'\bapi[_]?key\b',        # api_key, API_KEY
    r'\bpassword\b',          # password
    r'\bsecret\b',            # secret (word-bounded — not "secretary")
    r'\btoken\b',             # token (word-bounded)
    r'boss[\s]*rule',         # boss rule, Boss's rule
    r'\bnever\b',             # never — signals rules/directives
    r'\balways\b',            # always — signals rules/directives
    r'\bcritical\b',          # CRITICAL / Critical / critical
    r'\bconfig\b',            # config / Config
    r'rule[\s]*from',         # "Rule from:" / "rule from Boss"
]

P1_KEYWORDS = [
    r'\bdecision\b',          # decision, decisions
    r'\barchitecture\b',      # architecture
    r'\bupgrade\b',           # upgrade, upgraded
    r'\bdeploy\b',            # deploy, deployed, deployment
    r'\bproject\b',           # project
    r'\bmilestone\b',         # milestone
    r'\bsignificant\b',       # significant
]

P2_KEYWORDS = [
    r'\bcompleted\b',         # completed
    r'\bcreated\b',           # created
    r'\binstalled\b',         # installed
    r'\bupdated\b',           # updated
    r'\bfixed\b',             # fixed
    r'\bdaily\b',             # daily
]

P3_KEYWORDS = [
    r'\bdebug\b',             # debug
    r'\btest\b',              # test (but might be matched by P2 "tested" → no, "test" won't match "tested")
    r'\btemp\b',              # temp
    r'\bwip\b',               # wip
    r'\bdraft\b',             # draft
    r'\bmaybe\b',             # maybe
]

# ── Helpers ────────────────────────────────────────────────────────────────


def classify_text(text):
    """Classify a piece of text into P0/P1/P2/P3 using keyword rules.

    Highest-priority match wins (P0 > P1 > P2 > P3).
    Default: P2 (Normal).
    """
    text_lower = text.lower()

    for pattern in P0_KEYWORDS:
        if re.search(pattern, text_lower):
            return "P0"

    for pattern in P1_KEYWORDS:
        if re.search(pattern, text_lower):
            return "P1"

    for pattern in P2_KEYWORDS:
        if re.search(pattern, text_lower):
            return "P2"

    for pattern in P3_KEYWORDS:
        if re.search(pattern, text_lower):
            return "P3"

    return "P2"


def _file_basename(filepath):
    """Return the basename of a file path."""
    return os.path.basename(str(filepath))


def _sanitise_filepath(filepath):
    """Normalize & resolve a file path, returning a Path object or None."""
    p = Path(filepath).expanduser().resolve()
    return p if p.exists() else None


def extract_entries(filepath):
    """Extract entries from a markdown file by splitting on `## ` headings.

    Each `## Heading` block (heading + body until next `## `) is one entry.
    If the file has no `## ` headings, the whole file content is one entry.
    Returns a list of dicts: {heading, body, full_text, line, file}.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return []

    entries = []
    lines = content.split('\n')

    current_heading = None
    current_body_lines = []
    current_line = 0

    for i, line in enumerate(lines):
        if line.startswith('## ') and not line.startswith('### '):
            # Flush previous entry
            if current_heading is not None:
                body_text = '\n'.join(current_body_lines).strip()
                full_text = (
                    current_heading + '\n' + body_text
                    if body_text else current_heading
                )
                entries.append({
                    'heading': current_heading.strip(),
                    'body': body_text,
                    'full_text': full_text,
                    'line': current_line + 1,  # 1-indexed
                    'file': str(filepath),
                })
            current_heading = line
            current_body_lines = []
            current_line = i
        elif current_heading is not None:
            current_body_lines.append(line)

    # Flush last entry
    if current_heading is not None:
        body_text = '\n'.join(current_body_lines).strip()
        full_text = (
            current_heading + '\n' + body_text
            if body_text else current_heading
        )
        entries.append({
            'heading': current_heading.strip(),
            'body': body_text,
            'full_text': full_text,
            'line': current_line + 1,
            'file': str(filepath),
        })

    # Fallback: no ## headings → whole file as one entry
    if not entries and content.strip():
        first_line = lines[0].strip() if lines else ""
        entries.append({
            'heading': first_line[:80] or "(untitled)",
            'body': content.strip(),
            'full_text': content.strip(),
            'line': 1,
            'file': str(filepath),
        })

    return entries


def scan_files(memory_md=None, memory_dir=None):
    """Scan MEMORY.md and all daily logs (YYYY-MM-DD.md).

    Returns a flat list of all entries across all files.
    """
    if memory_md is None:
        memory_md = MEMORY_MD
    if memory_dir is None:
        memory_dir = MEMORY_DIR

    all_entries = []

    # MEMORY.md
    md_path = Path(memory_md)
    if md_path.exists():
        all_entries.extend(extract_entries(md_path))

    # Daily logs: memory/YYYY-MM-DD.md
    mem_dir = Path(memory_dir)
    if mem_dir.exists():
        for f in sorted(mem_dir.glob("20[0-9][0-9]-[0-9][0-9]-[0-9][0-9].md")):
            all_entries.extend(extract_entries(f))

    return all_entries


def build_distribution(entries):
    """Classify a list of entries and return a {P0: [...], P1: [...], ...} dict."""
    dist = {"P0": [], "P1": [], "P2": [], "P3": []}
    for entry in entries:
        priority = classify_text(entry['full_text'])
        dist[priority].append(entry)
    return dist


# ── Output ─────────────────────────────────────────────────────────────────


def _print_bar(dist, label=""):
    """Print a tree-style priority distribution summary."""
    p0 = len(dist["P0"])
    p1 = len(dist["P1"])
    p2 = len(dist["P2"])
    p3 = len(dist["P3"])
    total = p0 + p1 + p2 + p3

    title = f"📊 Priority Distribution"
    if label:
        title += f" — {label}"
    print(title)
    print(f"├── P0 (Critical):  {p0} entries")
    print(f"├── P1 (Important): {p1} entries")
    print(f"├── P2 (Normal):    {p2} entries")
    print(f"└── P3 (Transient): {p3} entries")
    print(f"    Total:          {total} entries\n")


def _print_top(dist, priority, label, count=5):
    """Print the top N entries for a given priority level."""
    entries = dist[priority]
    if not entries:
        return
    print(f"Top {label} entries:")
    for entry in entries[:count]:
        heading = entry['heading'].replace('## ', '').strip()
        # Truncate for display
        if len(heading) > 64:
            heading = heading[:61] + "..."
        fname = _file_basename(entry['file'])
        print(f'  - "{heading}" ({fname}:{entry["line"]})')
    print()


# ── Commands ───────────────────────────────────────────────────────────────


def cmd_classify(text):
    """Test classification of a single text string."""
    priority = classify_text(text)
    print(f'Priority: {priority}')
    print(f'Text: "{text}"')

    # Show which keywords triggered the match
    text_lower = text.lower()
    matched = []
    all_keywords = {
        "P0": P0_KEYWORDS, "P1": P1_KEYWORDS,
        "P2": P2_KEYWORDS, "P3": P3_KEYWORDS,
    }
    for pattern in all_keywords.get(priority, []):
        if re.search(pattern, text_lower):
            matched.append(pattern)
    if matched:
        print(f'Matched rules: {", ".join(matched)}')


def cmd_audit(workspace_root=None):
    """Full audit: scan MEMORY.md + daily logs, classify all entries."""
    entries = scan_files()
    dist = build_distribution(entries)
    _print_bar(dist, "MEMORY.md + Daily Logs")

    for priority, label in [("P0", "P0 (Critical)"), ("P1", "P1 (Important)")]:
        _print_top(dist, priority, label)

    # Per-file breakdown
    files = {}
    for entry in entries:
        fname = _file_basename(entry['file'])
        files.setdefault(fname, {"P0": 0, "P1": 0, "P2": 0, "P3": 0})
        files[fname][classify_text(entry['full_text'])] += 1

    print("Per-file breakdown:")
    for fname in sorted(files):
        c = files[fname]
        total_f = sum(c.values())
        parts = []
        for p in ("P0", "P1", "P2", "P3"):
            if c[p]:
                parts.append(f"{p}={c[p]}")
        print(f"  {fname}: {total_f} entries ({', '.join(parts)})")

    return dist


def cmd_audit_file(filepath):
    """Classify entries in a single file."""
    p = Path(filepath).expanduser().resolve()
    if not p.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    entries = extract_entries(p)
    dist = build_distribution(entries)
    _print_bar(dist, p.name)

    # Per-entry classification
    print("Per-entry classification:")
    for entry in entries:
        priority = classify_text(entry['full_text'])
        heading = entry['heading'].replace('## ', '').strip()
        if len(heading) > 70:
            heading = heading[:67] + "..."
        print(f'  [{priority}] "{heading}"  (line {entry["line"]})')


def cmd_status():
    """Quick status summary (no args)."""
    entries = scan_files()
    dist = build_distribution(entries)
    total = sum(len(v) for v in dist.values())
    if total == 0:
        print("📊 Priority Engine — No entries found in MEMORY.md or daily logs.")
        return

    print("📊 Priority Engine — Quick Status")
    print(f"   Scanned:   MEMORY.md + {len([f for f in MEMORY_DIR.glob('20*.md')])} daily logs")
    print(f"   P0 (Critical):  {len(dist['P0']):>3} entries  (always keep)")
    print(f"   P1 (Important): {len(dist['P1']):>3} entries  (30-day retention)")
    print(f"   P2 (Normal):    {len(dist['P2']):>3} entries  (7-day retention)")
    print(f"   P3 (Transient): {len(dist['P3']):>3} entries  (24h retention)")
    print(f"   ─────────────────────")
    print(f"   Total:          {total:>3} entries")

    # Quick highlight of P0 entries
    if dist["P0"]:
        print(f"\n📌 P0 entries ({len(dist['P0'])} found):")
        for entry in dist["P0"]:
            heading = entry['heading'].replace('## ', '').strip()
            if len(heading) > 64:
                heading = heading[:61] + "..."
            fname = _file_basename(entry['file'])
            print(f'   - "{heading}" ({fname}:{entry["line"]})')


# ── Main ───────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        cmd_status()
        return

    cmd = sys.argv[1]

    if cmd == "--classify":
        if len(sys.argv) < 3:
            print("Usage: priority_engine.py --classify <text>", file=sys.stderr)
            sys.exit(1)
        cmd_classify(sys.argv[2])

    elif cmd == "--audit":
        # If an extra arg looks like a file path, treat as --audit-file
        if len(sys.argv) > 2:
            arg = sys.argv[2]
            if (
                arg.endswith('.md')
                or arg.endswith('.txt')
                or arg.endswith('.json')
                or '/' in arg
                or '\\' in arg
            ):
                cmd_audit_file(arg)
                return
        cmd_audit()

    elif cmd == "--audit-file":
        if len(sys.argv) < 3:
            print("Usage: priority_engine.py --audit-file <path>", file=sys.stderr)
            sys.exit(1)
        cmd_audit_file(sys.argv[2])

    elif cmd in ("--help", "-h", "help"):
        print(__doc__)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(f"Usage: priority_engine.py [--classify <text> | --audit | --audit-file <path>]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
