#!/usr/bin/env python3
"""Trim MEMORY.md: keep 3 most recent Critical Lessons, 5 most recent daily Memory entries."""
import re

MEMORY_PATH = "/root/.openclaw/workspace/MEMORY.md"

with open(MEMORY_PATH, "r") as f:
    content = f.read()
    lines = content.splitlines()

# ── 1. Find all section boundaries ──────────────────────────────────
# Lines that are "## Memory (YYYY-MM-DD...)" entries
memory_section_re = re.compile(r"^## Memory \((\d{4}-\d{2}-\d{2})\)")
memory_lines = []  # list of (line_idx, date_str)
for i, line in enumerate(lines):
    m = memory_section_re.match(line)
    if m:
        memory_lines.append((i, m.group(1)))

print(f"Total daily memory sections: {len(memory_lines)}")

# ── 2. Find the Critical Lessons section ────────────────────────────
# It's between "## 🧠 Critical Lessons Learned (Cumulative)" and "## Major Projects & Milestones"
crit_lessons_start = None
crit_lessons_end = None
for i, line in enumerate(lines):
    if line.startswith("## 🧠 Critical Lessons Learned"):
        crit_lessons_start = i
    if crit_lessons_start and line.startswith("## Major Projects"):
        crit_lessons_end = i
        break

print(f"Critical Lessons section: lines {crit_lessons_start}-{crit_lessons_end}")

# ── 3. Trim Critical Lessons: keep only 3 most recent ──────────────
# Find lesson entries inside the section
if crit_lessons_start and crit_lessons_end:
    crit_section = lines[crit_lessons_start:crit_lessons_end]
    # Find lesson table rows with lesson numbers
    lesson_rows = []
    inside_table = False
    for j, cl in enumerate(crit_section):
        if cl.strip().startswith("|") and "|" in cl.strip()[1:]:
            cells = [c.strip() for c in cl.split("|")[1:-1]]
            if len(cells) >= 2 and cells[0].isdigit():
                lesson_rows.append((j, int(cells[0]), cl))
    
    print(f"Found {len(lesson_rows)} lesson rows in Critical Lessons")
    for lr in lesson_rows:
        print(f"  Lesson #{lr[1]} at offset {lr[0]}: {lr[2][:80]}")
    
    # Keep only 3 most recent (highest lesson numbers)
    if len(lesson_rows) > 3:
        lesson_rows.sort(key=lambda x: -x[1])  # sort by lesson# desc
        keep_numbers = set(lr[1] for lr in lesson_rows[:3])
        print(f"Keeping lessons: {sorted(keep_numbers)}")
        
        # Find the table header rows (| # | Lesson | etc.)
        table_start = None
        table_end = None
        for j, cl in enumerate(crit_section):
            if cl.strip().startswith("| :-: |") or cl.strip().startswith("|---"):
                table_start = j - 1  # include header row
            # Find where table ends (first non-pipe line after table)
        
        # Identify rows to keep (header + separator + 3 lessons + trim note)
        new_crit_lines = []
        for j, cl in enumerate(crit_section):
            # Skip the cumulative lessons list - we'll replace it
            stripped = cl.strip()
            if stripped.startswith("|") and "|" in stripped[1:]:
                cells = [c.strip() for c in cl.split("|")[1:-1]]
                if len(cells) >= 2 and cells[0].isdigit():
                    row_num = int(cells[0])
                    if row_num not in keep_numbers:
                        continue  # skip this lesson row
            new_crit_lines.append(cl)
        
        # Replace the section
        lines[crit_lessons_start:crit_lessons_end] = new_crit_lines
        print(f"Trimmed Critical Lessons to {len(keep_numbers)} lessons")

# ── 4. Keep only 5 most recent daily memory entries ────────────────
# Group memory sections by unique date, keep 5 most recent
# First re-scan because line indices may have shifted
memory_section_re2 = re.compile(r"^## Memory \((\d{4}-\d{2}-\d{2})\)")
memory_entries = []  # (line_idx, date_str)
for i, line in enumerate(lines):
    m = memory_section_re2.match(line)
    if m:
        memory_entries.append((i, m.group(1)))

print(f"\nMemory entries after lesson trim: {len(memory_entries)}")

# Get unique dates sorted desc
unique_dates = sorted(set(d for _, d in memory_entries), reverse=True)
print(f"Unique dates: {unique_dates}")
keep_dates = set(unique_dates[:5])
print(f"Keeping only 5 most recent dates: {sorted(keep_dates)}")

if len(unique_dates) > 5:
    # Build new content: keep everything up to first memory entry
    # then only include entries with dates in keep_dates
    
    first_mem_idx = memory_entries[0][0]
    new_lines = lines[:first_mem_idx]
    
    # For each memory section in original order, include if date is in keep_dates
    i = first_mem_idx
    while i < len(lines):
        m = memory_section_re2.match(lines[i])
        if m:
            date = m.group(1)
            if date in keep_dates:
                # Include this section
                new_lines.append(lines[i])
                i += 1
                # Continue until next ## Memory or end
                while i < len(lines) and not memory_section_re2.match(lines[i]):
                    new_lines.append(lines[i])
                    i += 1
            else:
                # Skip this section
                i += 1
                while i < len(lines) and not memory_section_re2.match(lines[i]):
                    i += 1
        else:
            new_lines.append(lines[i])
            i += 1
    
    lines = new_lines
    print(f"Trimmed away {len(unique_dates) - 5} old daily memory sections")

# ── 5. Ensure the "(Trimmed: ...)" notes are accurate ──────────────
# Update the trimmed notes if present

new_content = "\n".join(lines)
# Make sure file ends with newline
if not new_content.endswith("\n"):
    new_content += "\n"

with open(MEMORY_PATH, "w") as f:
    f.write(new_content)

new_size = len(new_content.encode("utf-8"))
print(f"\nNew file size: {new_size} bytes")
