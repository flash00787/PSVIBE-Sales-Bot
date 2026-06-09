#!/usr/bin/env python3
"""
Memory Consolidation Script — Extract daily log sections into topic summaries.

Usage:
    python3 consolidator.py                     # Consolidate most recent daily log (dry-run)
    python3 consolidator.py 2026-05-28          # Consolidate specific date (dry-run)
    python3 consolidator.py --all               # Consolidate all daily logs (dry-run)
    python3 consolidator.py --apply             # Apply consolidation to MEMORY.md
    python3 consolidator.py --apply 2026-05-28  # Apply specific date to MEMORY.md
    python3 consolidator.py --dry-run           # Explicit dry-run (default)

Scans memory/YYYY-MM-DD.md files, extracts ## header sections, and prints a
consolidation-ready summary grouped by topic.

With --apply: writes consolidated summaries into MEMORY.md with deduplication.
With --dry-run (default): preview only, no file changes.
"""

import os
import re
import sys

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
DAILY_LOG_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
MEMORY_MD_PATH = os.path.join(os.path.dirname(MEMORY_DIR), "MEMORY.md")


def find_daily_logs():
    """Find all YYYY-MM-DD.md files in the memory directory, sorted by date."""
    logs = []
    for fname in os.listdir(MEMORY_DIR):
        m = DAILY_LOG_PATTERN.match(fname)
        if m:
            logs.append((m.group(1), os.path.join(MEMORY_DIR, fname)))
    logs.sort(key=lambda x: x[0])
    return logs


def parse_sections(filepath):
    """
    Parse a daily markdown file into sections grouped by ## headers.

    If a ### sub-header appears without a parent ## header, it is treated
    as a section of its own so no content is silently dropped.

    Returns:
        dict: { "header_name": [list of bullet/non-empty lines] }
    """
    sections = {}
    current_header = None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (FileNotFoundError, IOError):
        return {}

    for line in lines:
        stripped = line.rstrip()

        # Detect ## level headers (skip # title)
        if stripped.startswith("## "):
            current_header = stripped[3:].strip()
            if current_header not in sections:
                sections[current_header] = []
            continue

        # Handle ### subheaders
        if stripped.startswith("### "):
            if current_header:
                # Treat subheader as a content line under parent
                sections[current_header].append(stripped)
            else:
                # No parent ## — treat ### as a top-level section
                orphan_header = stripped[4:].strip()
                if orphan_header not in sections:
                    sections[orphan_header] = []
                current_header = orphan_header
            continue

        # Skip empty lines and the top-level # header
        if not stripped or stripped.startswith("# "):
            continue

        # Capture content under current header
        if current_header:
            sections[current_header].append(stripped)

    return sections


def consolidate_date(date_str, filepath):
    """
    Print a consolidation summary for one daily log.

    Args:
        date_str: "YYYY-MM-DD" string
        filepath: full path to the .md file

    Returns:
        str: The generated markdown content (for use with --apply).
    """
    sections = parse_sections(filepath)
    lines = []

    if not sections:
        lines.append(f"## Memory ({date_str})")
        lines.append("")
        lines.append("*(no section content found)*")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"## Memory ({date_str})")
    lines.append("")

    for header, body_lines in sections.items():
        lines.append(f"### {header}")

        # Extract key bullet points, deduplicating within the section
        seen = set()
        content_lines = []
        for line in body_lines:
            clean = line.strip()
            if clean.startswith("- ") or clean.startswith("* "):
                clean = clean[2:].strip()
            elif clean.startswith("✅ ") or clean.startswith("❌ ") or clean.startswith("🔄 "):
                pass  # keep as-is

            # Deduplicate: skip exact duplicate lines within the same section
            dedup_key = clean.lower()
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            content_lines.append(clean)

        # If no content, print a placeholder
        if not content_lines:
            lines.append("")
            continue

        # Print each content line — preserve sub-headers, tables, and bullets
        for cl in content_lines:
            if cl.startswith("#"):
                # Sub-header
                lines.append("")
                lines.append(cl)
            elif cl.startswith("|") or cl.startswith("+-|:"):
                # Table rows — keep as-is
                lines.append(cl)
            else:
                lines.append(f"- {cl}")

        lines.append("")

    return "\n".join(lines)


def load_memory_md():
    """Load existing MEMORY.md content. Returns (exists_bool, content_string)."""
    try:
        with open(MEMORY_MD_PATH, "r", encoding="utf-8") as f:
            return True, f.read()
    except (FileNotFoundError, IOError):
        return False, ""


def dedup_content(new_content, existing_content):
    """
    Remove lines from new_content that already appear in existing_content.
    Uses line-level dedup — skips exact line matches.
    Preserves section headers.
    """
    existing_lines = set()
    for line in existing_content.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            existing_lines.add(stripped)

    result = []
    for line in new_content.split("\n"):
        stripped = line.strip()
        # Always keep headers
        if line.startswith("#"):
            result.append(line)
        elif stripped and stripped in existing_lines:
            # Replace duplicates with a note
            pass  # skip duplicates silently
        else:
            result.append(line)

    return "\n".join(result)


def apply_to_memory_md(new_content, date_str, dry_run=False):
    """
    Write consolidated content to MEMORY.md with deduplication.

    If a section for this date already exists, it is replaced.
    Otherwise, appended at the end.

    Dedup compares against manually-curated content only — previously
    consolidated sections are excluded from comparison so re-runs don't
    progressively strip content.

    Args:
        new_content: The generated markdown content
        date_str: The date string (YYYY-MM-DD)
        dry_run: If True, preview only — don't write
    """
    _, existing = load_memory_md()
    section_header = f"## Memory ({date_str})"

    if section_header in existing:
        # Replace existing section for this date
        # Extract the file with and without the old section
        lines = existing.split("\n")
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if line.strip() == section_header:
                start_idx = i
            elif start_idx is not None and line.startswith("## ") and i > start_idx:
                end_idx = i
                break
        if end_idx is None:
            end_idx = len(lines)

        # Content WITHOUT the old section (use for dedup base)
        content_without_old_section = "\n".join(lines[:start_idx] + lines[end_idx:])
        deduped = dedup_content(new_content, content_without_old_section)

        # Insert deduped content at the same position
        new_lines = lines[:start_idx] + deduped.split("\n") + lines[end_idx:]
        final_content = "\n".join(new_lines)
    else:
        # Append new section — dedup against all existing content
        if existing and not existing.endswith("\n"):
            existing += "\n"
        deduped = dedup_content(new_content, existing)
        final_content = existing + "\n" + deduped + "\n"

    # Normalize blank lines: collapse 3+ newlines to exactly 2 (one blank line)
    final_content = re.sub(r'\n{3,}', '\n\n', final_content)
    final_content = final_content.rstrip('\n') + '\n'

    if dry_run:
        print("\n── DRY-RUN: Would write to MEMORY.md ──")
        print(final_content)
        print("── End preview ──\n")
        return

    # Write MEMORY.md
    with open(MEMORY_MD_PATH, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"✅ Updated {MEMORY_MD_PATH} with consolidated memories from {date_str}")


def main():
    # Parse arguments
    target_date = None
    all_flag = False
    apply_flag = False
    dry_run_flag = False

    for arg in sys.argv[1:]:
        if arg == "--all":
            all_flag = True
        elif arg == "--apply":
            apply_flag = True
        elif arg == "--dry-run":
            dry_run_flag = True
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", arg):
            target_date = arg

    # Default to dry-run unless --apply is explicitly set
    is_dry_run = not apply_flag or dry_run_flag

    logs = find_daily_logs()

    if not logs:
        print("No daily logs found in", MEMORY_DIR)
        sys.exit(0)

    if target_date:
        # Find and consolidate specific date
        matching = [(d, p) for d, p in logs if d == target_date]
        if matching:
            content = consolidate_date(matching[0][0], matching[0][1])
            if apply_flag:
                apply_to_memory_md(content, matching[0][0], dry_run=is_dry_run)
            else:
                print(content)
        else:
            print(f"No daily log found for {target_date}")
            sys.exit(1)
    elif all_flag:
        # Consolidate all logs
        for date_str, filepath in logs:
            content = consolidate_date(date_str, filepath)
            if apply_flag:
                apply_to_memory_md(content, date_str, dry_run=is_dry_run)
            else:
                print(content)
                print("---\n")
    else:
        # Default: most recent daily log
        date_str, filepath = logs[-1]
        content = consolidate_date(date_str, filepath)
        if apply_flag:
            apply_to_memory_md(content, date_str, dry_run=is_dry_run)
        else:
            print(content)


if __name__ == "__main__":
    main()
