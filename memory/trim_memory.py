#!/usr/bin/env python3
"""Trim MEMORY.md: keep 3 most recent Critical Lessons, 5 most recent fixes, trim old entries."""
import re

with open('/root/.openclaw/workspace/MEMORY.md', 'r') as f:
    content = f.read()

lines = content.split('\n')

# Find section boundaries
section_starts = {}
for i, line in enumerate(lines):
    if line.startswith('## '):
        title = line.strip()
        section_starts[title] = i

# 1. Find Critical Lessons section (line 73 = index 72)
cles_title = '## 🧠 Critical Lessons Learned (Cumulative)'
cles_start = section_starts.get(cles_title)
if cles_start is None:
    print("ERROR: Critical Lessons section not found")
    exit(1)

# Next section after Critical Lessons
cles_end = None
for title, idx in sorted(section_starts.items(), key=lambda x: x[1]):
    if idx > cles_start:
        cles_end = idx
        break
if cles_end is None:
    cles_end = len(lines)

# Extract Critical Lessons content and find individual lessons
cles_lines = lines[cles_start:cles_end]
# Find lessons by their numbers (#XX)
lesson_boundaries = []
for i, line in enumerate(cles_lines):
    m = re.match(r'^\d+\.\s+\*\*', line.strip())
    if m:
        lesson_boundaries.append(i)

print(f"Found {len(lesson_boundaries)} lessons in Critical Lessons section")
# Keep the last 3 lessons
if len(lesson_boundaries) >= 3:
    keep_from = lesson_boundaries[-3]
    # Keep the section header + sub-headers + last 3 lessons
    # Find the last sub-header before keep_from
    last_subheader = 0
    for i, line in enumerate(cles_lines[:keep_from]):
        if line.startswith('### '):
            last_subheader = i
    
    # Build new Critical Lessons section
    new_cles = cles_lines[:last_subheader]  # Keep header + first sub-headers
    # Add a note
    new_cles.append('')
    new_cles.append('*(Trimmed: keeping only 3 most recent lessons)*')
    new_cles.append('')
    new_cles.extend(cles_lines[keep_from:])
    new_cles_section = '\n'.join(new_cles)
else:
    new_cles_section = '\n'.join(cles_lines)

# 2. There is no "FIX HISTORY" section. Look for the most recent fix-related content.
# The "## 🆕 June 23, 2026 — Major Bug Fixes & Features" is one. But there's no explicit FIX HISTORY.
# Instead, trim old Memory sections - keep only the 5 most recent.

# All Memory sections are date-based: ## Memory (YYYY-MM-DD)
memory_sections = []
for title, idx in section_starts.items():
    m = re.match(r'## Memory \((\d{4}-\d{2}-\d{2})\)', title)
    if m:
        memory_sections.append((m.group(1), idx, title))

# Sort by date descending
memory_sections.sort(key=lambda x: x[0], reverse=True)
print(f"Found {len(memory_sections)} Memory sections")
for date, idx, title in memory_sections:
    print(f"  {date} at line {idx+1}")

# Keep the 5 most recent Memory sections
keep_dates = set(ms[0] for ms in memory_sections[:5])
print(f"Keeping Memory sections: {sorted(keep_dates)}")

# Now rebuild the file
# Strategy: keep architecture, people, business, trimmed critical lessons, 
# major projects, known issues, working preferences, and only the 5 most recent Memory sections

sections_to_keep_titles = [
    '## 🏗️ Multi-Project Architecture (Phase 1-5 Complete — 2026-06-25)',
    '## People',
    '## Business: PS VIBE - PS5 Gaming Lounge',
    '## Major Projects & Milestones',
    '## ⚠️ Known Issues (Persistent)',
    '## Working Preferences',
]

# Build new file
new_lines = []
current_section_title = None
skip_until_next_section = False
in_memory_section = False
current_memory_date = None

for i, line in enumerate(lines):
    if line.startswith('## '):
        current_section_title = line.strip()
        
        # Check if this is a Memory section
        m = re.match(r'## Memory \((\d{4}-\d{2}-\d{2})\)', line.strip())
        if m:
            current_memory_date = m.group(1)
            if current_memory_date in keep_dates:
                in_memory_section = True
                new_lines.append(line)
            else:
                in_memory_section = False
            continue
        
        in_memory_section = False
        current_memory_date = None
        
        # Check if this is a section we want to keep
        if current_section_title in sections_to_keep_titles:
            skip_until_next_section = False
            new_lines.append(line)
        elif current_section_title == cles_title:
            skip_until_next_section = False
            new_lines.append(new_cles_section)
            # Skip original lines until next section
            skip_until_next_section = True
        elif current_section_title == '## 🆕 June 23, 2026 — Major Bug Fixes & Features':
            # Skip this section - it's not a formal FIX HISTORY
            skip_until_next_section = True
        else:
            skip_until_next_section = True
        continue
    
    if skip_until_next_section:
        continue
    
    if in_memory_section:
        new_lines.append(line)
        continue
    
    # For sections we're keeping
    new_lines.append(line)

result = '\n'.join(new_lines)

# Clean up excessive blank lines (more than 2 consecutive)
result = re.sub(r'\n{3,}', '\n\n', result)

with open('/root/.openclaw/workspace/MEMORY.md', 'w') as f:
    f.write(result)

new_size = len(result.encode('utf-8'))
print(f"New size: {new_size} bytes (was {len(content.encode('utf-8'))})")
print("Done trimming")
