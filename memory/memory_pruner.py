#!/usr/bin/env python3
"""
memory_pruner.py — Smart Dedup & Pruning for MEMORY.md

Scans MEMORY.md for duplicate/similar content, merges entries, and archives
old P2/P3 entries to keep MEMORY.md lean.

Usage:
  python3 memory_pruner.py                        # Same as --dry-run
  python3 memory_pruner.py --dry-run              # Preview what would be pruned
  python3 memory_pruner.py --apply                # Actually prune MEMORY.md
  python3 memory_pruner.py --status               # Show current MEMORY.md stats
  python3 memory_pruner.py --target-size 25       # Set target size in KB (default 20)
  python3 memory_pruner.py --help                 # Show this help

Dedup Rules:
  1. Exact line match → Keep first occurrence, remove duplicates
  2. Similar lines (>80% word overlap) → Merge into one (keep first)
  3. Same-topic P2 entries → Keep newest 3, archive older
  4. Same-topic P3 entries → Archive all (transient)

Archive:
  Pruned content goes to ``memory/ARCHIVE.md`` with timestamp header.
"""

import os
import sys
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict, OrderedDict

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

WORKSPACE = Path(__file__).resolve().parent.parent
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_MD = WORKSPACE / "MEMORY.md"
ARCHIVE_MD = MEMORY_DIR / "ARCHIVE.md"
DEFAULT_TARGET_KB = 20

# ── Priority keywords (mirrors priority_engine.py) ─────────────────────────

P0_KEYWORDS = [
    r"\bapi[_]?key\b",
    r"\bpassword\b",
    r"\bsecret\b",
    r"\btoken\b",
    r"boss[\s]*rule",
    r"\bnever\b",
    r"\balways\b",
    r"\bcritical\b",
    r"\bconfig\b",
    r"rule[\s]*from",
]

P1_KEYWORDS = [
    r"\bdecision\b",
    r"\barchitecture\b",
    r"\bupgrade\b",
    r"\bdeploy\b",
    r"\bproject\b",
    r"\bmilestone\b",
    r"\bsignificant\b",
    r"\bprotocol\b",
    r"\bdesign\b",
]

P2_KEYWORDS = [
    r"\bcompleted\b",
    r"\bcreated\b",
    r"\binstalled\b",
    r"\bupdated\b",
    r"\bfixed\b",
    r"\bdaily\b",
    r"\bverified\b",
    r"\bpassed\b",
    r"\brunning\b",
]

P3_KEYWORDS = [
    r"\bdebug\b",
    r"\btest\b",
    r"\btemp\b",
    r"\bwip\b",
    r"\bdraft\b",
    r"\bmaybe\b",
]

# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════


def classify_text(text):
    """Classify text P0 → P1 → P2 → P3 by keyword match.  Default: P2."""
    tl = text.lower()
    for pat in P0_KEYWORDS:
        if re.search(pat, tl):
            return "P0"
    for pat in P1_KEYWORDS:
        if re.search(pat, tl):
            return "P1"
    for pat in P2_KEYWORDS:
        if re.search(pat, tl):
            return "P2"
    for pat in P3_KEYWORDS:
        if re.search(pat, tl):
            return "P3"
    return "P2"


def tokenize(text):
    """Return set of lowercase word tokens (≥3 chars)."""
    return set(re.findall(r"[a-z0-9]{3,}", text.lower()))


def word_overlap_ratio(a, b):
    """Jaccard similarity on word tokens.  Returns float 0.0 – 1.0."""
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    union = ta | tb
    return len(inter) / len(union) if union else 0.0


def extract_topic(heading):
    """Extract topic from heading: text before ' — ' or ': '."""
    clean = heading.replace("## ", "").strip()
    for sep in (" — ", ": ", " – "):
        if sep in clean:
            return clean.split(sep)[0].strip()
    return clean


def _is_meaningful_line(line):
    """True if a body line carries semantic content worth dedup'ing."""
    stripped = line.strip()
    if not stripped:
        return False
    # Skip pure structural / markdown formatting
    if stripped.startswith("```") or stripped.startswith("---"):
        return False
    if stripped.startswith("|") and stripped.endswith("|"):  # table row
        return False
    # Must have at least 4 alphabetic characters
    words = re.findall(r"[a-zA-Z]{2,}", stripped)
    if len(words) < 4:
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════
#  Entry parsing
# ═══════════════════════════════════════════════════════════════════════════


def parse_entries(content, source="MEMORY.md"):
    """Parse markdown content into entry dicts split on ``## `` headings.

    Each ``## Heading`` block (heading + body until next ``## ``) is one
    entry.  If the file has no ``## `` headings the whole content is a single
    entry.

    Returns list of dicts::

        {
          heading, body, full_text,
          start_line, end_line,   # 1-indexed
          source,                 # filename
          priority, topic,        # computed
        }
    """
    entries = []
    lines = content.split("\n")

    cur_head = None
    cur_body = []
    cur_start = 0

    for i, line in enumerate(lines):
        if line.startswith("## ") and not line.startswith("### "):
            # ── flush previous entry ──
            if cur_head is not None:
                body = "\n".join(cur_body)
                full = cur_head + "\n" + body if body.strip() else cur_head
                entries.append(
                    {
                        "heading": cur_head.strip(),
                        "body": body,
                        "full_text": full,
                        "start_line": cur_start + 1,
                        "end_line": i,
                        "source": source,
                    }
                )
            cur_head = line
            cur_body = []
            cur_start = i
        elif cur_head is not None:
            cur_body.append(line)

    # ── flush final entry ──
    if cur_head is not None:
        body = "\n".join(cur_body)
        full = cur_head + "\n" + body if body.strip() else cur_head
        entries.append(
            {
                "heading": cur_head.strip(),
                "body": body,
                "full_text": full,
                "start_line": cur_start + 1,
                "end_line": len(lines),
                "source": source,
            }
        )

    # ── fallback: no ## headings → whole file is one entry ──
    if not entries and content.strip():
        entries.append(
            {
                "heading": "(untitled)",
                "body": content.strip(),
                "full_text": content.strip(),
                "start_line": 1,
                "end_line": len(lines),
                "source": source,
            }
        )

    # ── annotate ──
    for e in entries:
        e["priority"] = classify_text(e["full_text"])
        e["topic"] = extract_topic(e["heading"])

    return entries


# ═══════════════════════════════════════════════════════════════════════════
#  Dedup detection
# ═══════════════════════════════════════════════════════════════════════════


def find_exact_line_duplicates(entries):
    """Find exact duplicate body lines across all entries.

    Only considers *meaningful* lines (≥4 alphabetic words, not pure
    markdown).  The **first** occurrence is kept; every later duplicate is
    flagged.

    Returns list of dicts::

        {line, normalized, entry_idx, line_idx, first_entry_idx, first_line_idx}
    """
    seen = {}  # normalized_lower → (entry_idx, line_idx)
    duplicates = []

    for ei, entry in enumerate(entries):
        body_lines = entry["body"].split("\n")
        for li, line in enumerate(body_lines):
            stripped = line.strip()
            if not _is_meaningful_line(stripped):
                continue

            norm = stripped.lower()
            if norm in seen:
                prev_ei, prev_li = seen[norm]
                duplicates.append(
                    {
                        "line": stripped,
                        "normalized": norm,
                        "entry_idx": ei,
                        "line_idx": li,
                        "first_entry_idx": prev_ei,
                        "first_line_idx": prev_li,
                    }
                )
            else:
                seen[norm] = (ei, li)

    return duplicates


def find_similar_lines(entries, threshold=0.80, min_words=5):
    """Find body-line pairs with ≥ *threshold* word-overlap ratio.

    Each pair is a merge candidate — the second occurrence (line *b*) should
    be dropped.

    Returns list of dicts::

        {line_a, line_b, entry_a, entry_b, line_idx_a, line_idx_b, similarity}
    """
    # Collect meaningful body lines
    all_lines = []  # (text, entry_idx, line_idx, lowercased)
    for ei, entry in enumerate(entries):
        body_lines = entry["body"].split("\n")
        for li, line in enumerate(body_lines):
            stripped = line.strip()
            if not _is_meaningful_line(stripped):
                continue
            words = re.findall(r"[a-z]{3,}", stripped.lower())
            if len(words) < min_words:
                continue
            all_lines.append((stripped, ei, li, stripped.lower()))

    # Pairwise compare — O(n²) but n is tiny for MEMORY.md
    # Skip exact-duplicate pairs (those are handled by find_exact_line_duplicates)
    merges = []
    n = len(all_lines)
    for i in range(n):
        for j in range(i + 1, n):
            # If the lowercased lines are identical, it's an exact duplicate — skip
            if all_lines[i][3] == all_lines[j][3]:
                continue
            sim = word_overlap_ratio(all_lines[i][3], all_lines[j][3])
            if sim >= threshold:
                merges.append(
                    {
                        "line_a": all_lines[i][0],
                        "line_b": all_lines[j][0],
                        "entry_a": all_lines[i][1],
                        "entry_b": all_lines[j][1],
                        "line_idx_a": all_lines[i][2],
                        "line_idx_b": all_lines[j][2],
                        "similarity": round(sim, 3),
                    }
                )

    return merges


def find_archivable_entries(entries):
    """Return sorted list of entry indices that should be archived.

    - **P3 entries:** archive **all**.
    - **P2 entries:** group by topic; keep newest 3 per topic, archive older.
    - **P0 / P1:** never archived.

    *Newest* = highest end_line (appears later in file).
    """
    to_archive = set()

    # ── P3: archive everything ──
    for i, entry in enumerate(entries):
        if entry["priority"] == "P3":
            to_archive.add(i)

    # ── P2 grouped by topic ──
    topic_p2 = defaultdict(list)
    for i, entry in enumerate(entries):
        if entry["priority"] == "P2" and i not in to_archive:
            topic_p2[entry["topic"]].append(i)

    for topic, indices in topic_p2.items():
        if len(indices) <= 3:
            continue
        # Sort by end_line ascending → newest are at the end
        indices_sorted = sorted(indices, key=lambda idx: entries[idx]["end_line"])
        # Archive older ones (all but last 3)
        for idx in indices_sorted[:-3]:
            to_archive.add(idx)

    return sorted(to_archive)


# ═══════════════════════════════════════════════════════════════════════════
#  Rebuild
# ═══════════════════════════════════════════════════════════════════════════


def rebuild_memory_md(content, entries, exact_dupes, similar_merges, archive_indices):
    """Produce new MEMORY.md content + pruned text for the archive.

    Parameters
    ----------
    content : str
        Original file content.
    entries : list[dict]
        Parsed entries (already annotated with priority/topic).
    exact_dupes : list[dict]
        From ``find_exact_line_duplicates``.
    similar_merges : list[dict]
        From ``find_similar_lines``.
    archive_indices : list[int]
        From ``find_archivable_entries``.

    Returns
    -------
    new_content : str
        Cleaned MEMORY.md text.
    pruned_text : str
        Text to append into ARCHIVE.md.
    """
    lines = content.split("\n")

    # ── Build removal sets ──
    # (entry_idx, line_idx) for individual body lines to drop
    drop_lines = set()

    for d in exact_dupes:
        drop_lines.add((d["entry_idx"], d["line_idx"]))

    for m in similar_merges:
        drop_lines.add((m["entry_b"], m["line_idx_b"]))

    # Entry indices to archive wholesale
    archive_set = set(archive_indices)

    # ── Rebuild ──
    kept_lines = []  # lines for the new MEMORY.md
    pruned_parts = []  # text to write into ARCHIVE.md

    for ei, entry in enumerate(entries):
        if ei in archive_set:
            # ── archive entire entry ──
            pruned_parts.append(
                f"\n## [{entry['priority']}] {entry['heading'].replace('## ', '')}"
            )
            if entry["body"].strip():
                pruned_parts.append(entry["body"].rstrip())
            continue

        # ── heading always kept ──
        kept_lines.append(entry["heading"])

        # ── body lines: skip dupes ──
        body_lines = entry["body"].split("\n")
        for li, bline in enumerate(body_lines):
            if (ei, li) in drop_lines:
                pruned_parts.append(f"  (dedup) {bline.strip()}")
            else:
                kept_lines.append(bline)

    # ── Preamble: lines before the first entry ──
    preamble_end = entries[0]["start_line"] - 1 if entries else 0
    preamble = "\n".join(lines[:preamble_end]).rstrip()

    new_content = preamble + "\n" + "\n".join(kept_lines).rstrip() + "\n"
    pruned_text = "\n".join(pruned_parts).strip()

    return new_content, pruned_text


# ═══════════════════════════════════════════════════════════════════════════
#  Commands
# ═══════════════════════════════════════════════════════════════════════════


def cmd_status():
    """Show current MEMORY.md size, entry count, and estimated savings."""
    if not MEMORY_MD.exists():
        print("📊 MEMORY.md not found — nothing to prune.")
        return

    raw = MEMORY_MD.read_bytes()
    content = raw.decode("utf-8")
    size_bytes = len(raw)
    size_kb = size_bytes / 1024
    entries = parse_entries(content)

    # ── baseline stats ──
    print("📊 MEMORY.md Status")
    print(f'   Path:          {MEMORY_MD}')
    print(f"   File size:     {size_kb:.1f} KB ({size_bytes:,} bytes)")
    print(f"   Entries:       {len(entries)}")
    print(f"   Characters:    {len(content):,}")
    print(f"   Lines:         {len(content.split(chr(10)))}")

    prio = defaultdict(int)
    for e in entries:
        prio[e["priority"]] += 1
    print(f"   P0 (Critical): {prio.get('P0', 0)}")
    print(f"   P1 (Important):{prio.get('P1', 0)}")
    print(f"   P2 (Normal):   {prio.get('P2', 0)}")
    print(f"   P3 (Transient):{prio.get('P3', 0)}")

    # ── topic distribution ──
    topic_counts = defaultdict(int)
    for e in entries:
        topic_counts[e["topic"]] += 1
    multi = {t: c for t, c in topic_counts.items() if c > 1}
    if multi:
        print(f"\n   Topics with ≥2 entries:")
        for t, c in sorted(multi.items(), key=lambda x: -x[1]):
            print(f"     - \"{t}\": {c} entries")

    # ── quick scan ──
    exact = find_exact_line_duplicates(entries)
    similar = find_similar_lines(entries)
    arch = find_archivable_entries(entries)

    print(f"\n📈 Estimated Savings (dry-run preview):")
    print(f"   Exact duplicates:    {len(exact)} lines")
    print(f"   Similar merges:      {len(similar)} pairs")
    print(f"   Archivable entries:  {len(arch)} entries")
    savings = len(exact) + len(similar) + len(arch)
    est_kb = (savings * 80) / 1024
    print(f"   Estimated savings:   ~{est_kb:.1f} KB")

    if size_kb > DEFAULT_TARGET_KB:
        over = size_kb - DEFAULT_TARGET_KB
        print(f"\n⚠️   {over:.1f} KB over target ({DEFAULT_TARGET_KB} KB target)")


def cmd_dry_run(target_kb=DEFAULT_TARGET_KB):
    """Preview what would be pruned — no files are changed."""
    if not MEMORY_MD.exists():
        print("📋 MEMORY.md not found — nothing to preview.")
        return

    content = MEMORY_MD.read_text(encoding="utf-8")
    entries = parse_entries(content)

    exact = find_exact_line_duplicates(entries)
    similar = find_similar_lines(entries)
    arch = find_archivable_entries(entries)

    total = len(exact) + len(similar) + len(arch)
    size_kb = len(content.encode("utf-8")) / 1024

    print(f"🔍 DRY RUN — Preview (target: {target_kb} KB)")
    print(f"   {'═' * 54}")
    print(f"   MEMORY.md entries:  {len(entries)}")
    print(f"   File size:          {size_kb:.1f} KB")
    print()

    # ── Exact dupes ──
    if exact:
        print(f"   📌 Exact Duplicate Lines  ({len(exact)}):")
        for d in exact[:12]:
            e = entries[d["entry_idx"]]
            print(
                f'     - "{d["line"][:64]}"'
            )
            print(
                f"       Topic: {e['topic']!r}  "
                f"(first at entry #{d['first_entry_idx']+1} line {d['first_line_idx']+1})"
            )
        if len(exact) > 12:
            print(f"     … and {len(exact) - 12} more")
        print()

    # ── Similar merges ──
    if similar:
        print(f"   📌 Similar Lines to Merge  ({len(similar)} pairs):")
        for m in similar[:12]:
            print(f'     - "{m["line_a"][:54]}"')
            print(f'       "{m["line_b"][:54]}"')
            print(f"       Similarity: {m['similarity']:.0%}")
        if len(similar) > 12:
            print(f"     … and {len(similar) - 12} more")
        print()

    # ── Archivable entries ──
    if arch:
        print(f"   📌 Entries to Archive  ({len(arch)}):")
        for idx in arch:
            e = entries[idx]
            heading_short = e["heading"].replace("## ", "")[:64]
            print(
                f'     - [{e["priority"]}] "{heading_short}"'
            )
            print(
                f"       Topic: {e['topic']!r}  "
                f"lines {e['start_line']}–{e['end_line']}"
            )
        print()

    if total == 0:
        print("   ✅ No pruning needed — MEMORY.md is clean!")

        # Check target size
        if size_kb > target_kb:
            gap = size_kb - target_kb
            print(f"   ⚠️  File is {gap:.1f} KB over target ({target_kb} KB) "
                  f"but no automated candidates found.")
        return

    print(f"   {'─' * 54}")
    print(f"   Total to prune/merge:  {total} items")
    est_savings_kb = (total * 80) / 1024
    print(f"   Estimated savings:     ~{est_savings_kb:.1f} KB")
    print(f"   Post-prune estimate:   ~{size_kb - est_savings_kb:.1f} KB")
    print(f"\n   💡 Run with --apply to execute pruning")


def cmd_apply(target_kb=DEFAULT_TARGET_KB):
    """Prune MEMORY.md and write pruned content to ARCHIVE.md."""
    if not MEMORY_MD.exists():
        print("❌ MEMORY.md not found.")
        return

    content = MEMORY_MD.read_text(encoding="utf-8")
    original_size = len(content.encode("utf-8"))
    entries = parse_entries(content)

    exact = find_exact_line_duplicates(entries)
    similar = find_similar_lines(entries)
    arch = find_archivable_entries(entries)

    total = len(exact) + len(similar) + len(arch)

    if total == 0:
        print("✅ Nothing to prune — MEMORY.md is already clean.")
        return

    # ── Rebuild ──
    new_content, pruned_text = rebuild_memory_md(
        content, entries, exact, similar, arch
    )

    # ── Write MEMORY.md ──
    MEMORY_MD.write_text(new_content, encoding="utf-8")
    new_size = len(new_content.encode("utf-8"))

    # ── Write / append ARCHIVE.md ──
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    archive_block = (
        f"\n\n# Archived Memory Entries\n"
        f"*Archived: {now_ts}*\n"
        f"\n{pruned_text}\n"
    )

    if ARCHIVE_MD.exists():
        ARCHIVE_MD.write_text(
            ARCHIVE_MD.read_text(encoding="utf-8").rstrip() + archive_block,
            encoding="utf-8",
        )
    else:
        ARCHIVE_MD.write_text(archive_block.lstrip(), encoding="utf-8")

    mem_dir = MEMORY_DIR
    if mem_dir.exists():
        daily_count = len(list(mem_dir.glob("20[0-9][0-9]-[0-9][0-9]-[0-9][0-9].md")))
    else:
        daily_count = 0

    # ── Report ──
    pct = (1 - new_size / original_size) * 100 if original_size else 0
    print(f"✅ Pruning Complete!")
    print(f"   {'─' * 40}")
    print(f"   Exact duplicates removed:  {len(exact)}")
    print(f"   Similar lines merged:      {len(similar)}")
    print(f"   Entries archived:          {len(arch)}")
    print(f"   Scanned daily logs:        {daily_count}")
    print(f"   {'─' * 40}")
    print(f"   MEMORY.md before:  {original_size / 1024:.1f} KB ({original_size:,} B)")
    print(f"   MEMORY.md after:   {new_size / 1024:.1f} KB ({new_size:,} B)")
    print(f"   Savings:           {(original_size - new_size) / 1024:.1f} KB ({pct:.0f}%)")
    print(f"   Archive written:   memory/ARCHIVE.md")


# ═══════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════


def main():
    target_kb = DEFAULT_TARGET_KB
    cmd = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--target-size":
            i += 1
            if i < len(args):
                try:
                    target_kb = int(args[i])
                except ValueError:
                    print(f"Invalid target size: {args[i]}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("--target-size requires a value", file=sys.stderr)
                sys.exit(1)
        elif a in ("--dry-run", "--apply", "--status", "--help", "-h"):
            cmd = a
        else:
            print(f"Unknown argument: {a}", file=sys.stderr)
            sys.exit(1)
        i += 1

    if cmd in ("--help", "-h"):
        print(__doc__)
    elif cmd == "--status":
        cmd_status()
    elif cmd == "--apply":
        cmd_apply(target_kb)
    else:
        # default = dry-run
        cmd_dry_run(target_kb)


if __name__ == "__main__":
    main()
