#!/usr/bin/env python3
"""
Memory Index — Topic → File mapping for Kora's memory system.

Scans .md and .json files in memory/ plus root MEMORY.md.
Extracts topics from headings, bolded keywords, and task names.
Produces a searchable memory-index.json.

Usage:
    python3 memory/memory_index.py                  # Quick status
    python3 memory/memory_index.py --rebuild         # Force full rebuild
    python3 memory/memory_index.py --search <topic>  # Search index
    python3 memory/memory_index.py --stats           # Show statistics
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
INDEX_PATH = os.path.join(MEMORY_DIR, "memory-index.json")
ROOT_MEMORY = os.path.join(WORKSPACE, "MEMORY.md")

# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _context_line(lines, idx, width=200):
    """Return current line + next non-empty line as context, truncated."""
    parts = [lines[idx].strip()]
    if idx + 1 < len(lines):
        nxt = lines[idx + 1].strip()
        if nxt:
            parts.append(nxt)
    ctx = " ".join(parts)
    return ctx[:width]


def extract_topics_from_md(filepath):
    """Extract (topic, line_number, context) tuples from a markdown file."""
    topics = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        lineno = i + 1

        # ── ## Level-2 headings ──────────────────────────────────────────
        m = re.match(r"^##\s+(.+)", stripped)
        if m:
            topic = m.group(1).strip()
            if topic:
                topics.append((topic, lineno, _context_line(lines, i)))
            continue

        # ── ### Level-3 subheadings ───────────────────────────────────────
        m = re.match(r"^###\s+(.+)", stripped)
        if m:
            topic = m.group(1).strip()
            # filter out purely-decorative subheadings
            if topic and not topic.startswith("🟢") and not topic.startswith("🔴"):
                topics.append((topic, lineno, _context_line(lines, i)))
            continue

        # ── Bolded keywords (**…**) ──────────────────────────────────────
        for bold_text in re.findall(r"\*\*(.+?)\*\*", stripped):
            bt = bold_text.strip()
            # skip very short blobs, backtick-wrapped, and pure markup
            if len(bt) >= 3 and "`" not in bt and bt not in (" "):
                topics.append((bt, lineno, _context_line(lines, i)))

    return topics


def extract_topics_from_json(filepath):
    """Extract topics from structured JSON files."""
    topics = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, Exception):
        return topics

    # ── subagent-journal.json style entries ──────────────────────────────
    if isinstance(data, dict) and "entries" in data:
        for idx, entry in enumerate(data["entries"]):
            for field in ("taskName", "task"):
                val = entry.get(field, "")
                if val and isinstance(val, str) and len(val.strip()) >= 3:
                    ctx = f"status: {entry.get('status', '?')} | summary: {entry.get('summary', '')}"
                    topics.append((val.strip(), idx + 1, ctx[:200]))

    # ── active_tasks.json style ──────────────────────────────────────────
    if isinstance(data, dict) and "active" in data:
        for task_id, entry in data["active"].items():
            if isinstance(entry, dict):
                for field in ("taskName", "task", "goal"):
                    val = entry.get(field, "")
                    if val and isinstance(val, str) and len(val.strip()) >= 3:
                        topics.append((val.strip(), 0, f"active task: {task_id}"))

    return topics


# ---------------------------------------------------------------------------
# Index build / load / save
# ---------------------------------------------------------------------------

def build_index():
    """Walk memory/ .md and .json files + root MEMORY.md, build index dict."""
    # topic_lower → {"topic": display-name, "files": [{path, line, context}]}
    index_map = {}

    def _collect(filepath):
        rel = os.path.relpath(filepath, WORKSPACE)

        if filepath.endswith(".md"):
            raw = extract_topics_from_md(filepath)
        elif filepath.endswith(".json"):
            raw = extract_topics_from_json(filepath)
        else:
            return

        for topic, lineno, ctx in raw:
            key = topic.lower().strip().rstrip(":")  # normalize for dedup
            if key not in index_map:
                index_map[key] = {"topic": topic, "files": []}

            # guard duplicate file refs (same path + line)
            existing = {(f["path"], f["line"]) for f in index_map[key]["files"]}
            if (rel, lineno) not in existing:
                index_map[key]["files"].append(
                    {"path": rel, "line": lineno, "context": ctx}
                )

    # 1. Scan memory/ directory
    for fname in sorted(os.listdir(MEMORY_DIR)):
        fpath = os.path.join(MEMORY_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        if fname == "memory-index.json":
            continue
        if fname.endswith(".md") or fname.endswith(".json"):
            _collect(fpath)

    # 2. Also scan root MEMORY.md (primary memory file)
    if os.path.isfile(ROOT_MEMORY):
        _collect(ROOT_MEMORY)

    # Sort alphabetically by display topic
    sorted_entries = sorted(index_map.values(), key=lambda e: e["topic"].lower())

    return {
        "version": 1,
        "updated": datetime.now(timezone.utc).isoformat(),
        "entries": sorted_entries,
    }


def save_index(index):
    """Write index JSON to disk."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"✅ Index saved → {INDEX_PATH}")
    print(f"   Topics: {len(index['entries'])}")


def load_index():
    """Return index dict or None if missing/corrupt."""
    if not os.path.isfile(INDEX_PATH):
        return None
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return None


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_rebuild():
    print("🔨 Rebuilding memory index …")
    idx = build_index()
    save_index(idx)
    return idx


def cmd_search(topic):
    idx = load_index()
    if idx is None:
        print("❌ No index found. Run --rebuild first.")
        return

    pattern = topic.lower().strip()
    matches = [e for e in idx.get("entries", []) if pattern in e["topic"].lower()]

    if not matches:
        print(f"🔍 No topics matching '{topic}'")
        return

    print(f"🔍 {len(matches)} topic(s) matching '{topic}':\n")
    for entry in matches:
        print(f"▸ {entry['topic']}")
        for ref in entry["files"]:
            print(f"    📄 {ref['path']}  (line {ref['line']})")
            if ref.get("context"):
                print(f"       {ref['context'][:130]}")
        print()


def cmd_stats():
    idx = load_index()
    if idx is None:
        print("❌ No index found. Run --rebuild first.")
        return

    entries = idx.get("entries", [])
    n_topics = len(entries)
    n_refs = sum(len(e.get("files", [])) for e in entries)
    files = sorted({f["path"] for e in entries for f in e.get("files", [])})

    print("=" * 42)
    print("        Memory Index Statistics")
    print("=" * 42)
    print(f"  Topics indexed    : {n_topics}")
    print(f"  File references   : {n_refs}")
    print(f"  Unique files      : {len(files)}")
    print(f"  Last updated      : {idx.get('updated', '?')}")
    print(f"  Index version     : {idx.get('version', '?')}")
    if files:
        print(f"\n  Indexed files ({len(files)}):")
        for f in files:
            print(f"    📄 {f}")
    print()


def cmd_status():
    idx = load_index()
    if idx is None:
        print("📭 No index found. Run with --rebuild to create one.")
        return

    n = len(idx.get("entries", []))
    updated = idx.get("updated", "")

    try:
        dt = datetime.fromisoformat(updated)
        delta = datetime.now(timezone.utc) - dt
        if delta.days > 0:
            age = f"{delta.days}d {delta.seconds // 3600}h ago"
        elif delta.seconds >= 3600:
            age = f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            age = f"{delta.seconds // 60}m ago"
        else:
            age = f"{delta.seconds}s ago"
    except (ValueError, TypeError):
        age = "unknown"

    print(f"📇 Memory Index: {n} topics · updated {age}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        cmd_status()
        return

    cmd = sys.argv[1]

    if cmd == "--rebuild":
        cmd_rebuild()
    elif cmd == "--search":
        if len(sys.argv) < 3:
            print("Usage: memory/memory_index.py --search <topic>")
            sys.exit(1)
        cmd_search(sys.argv[2])
    elif cmd == "--stats":
        cmd_stats()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: memory_index.py [--rebuild | --search <topic> | --stats]")
        sys.exit(1)


if __name__ == "__main__":
    main()
