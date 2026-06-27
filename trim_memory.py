#!/usr/bin/env python3
"""Trim MEMORY.md: keep 3 most recent lessons + 5 most recent fixes."""

import re, sys

path = "/root/.openclaw/workspace/MEMORY.md"
with open(path) as f:
    content = f.read()

orig_size = len(content.encode())

# --- 1. Remove duplicate block at end of Memory (2026-06-27) ---
# The "#39-#46" block and "Other Fixes" appear twice. Remove the second copy.
dup_marker = "- **#39: Member card → Telegram link needs booking's `member_id` field**"
first_idx = content.find(dup_marker)
second_idx = content.find(dup_marker, first_idx + 1)
if second_idx > 0:
    # Find where the second duplicate block starts (go back to find the line start)
    line_start = content.rfind("\n", 0, second_idx)
    dup_start = content.rfind("- **#39:", 0, second_idx)
    if dup_start > 0:
        # find the paragraph before this list starts
        para_start = content.rfind("\n\n", 0, dup_start)
        if para_start < 0:
            para_start = content.rfind("\n", 0, dup_start)
        # Remove from para_start to end
        content = content[:para_start].rstrip() + "\n"
        print(f"[1] Removed duplicate Jun 27 block starting at byte {para_start}")

# --- 2. CRITICAL LESSONS: keep only 3 most recent ---
# All lessons numbered #33 through #46 across the file
# 3 most recent: #44, #45, #46
recent_3_lessons = {
    44: "**`unwrap_response()` changes response structure** — Functions consuming API responses must NOT access `.data` again after unwrap. Use `data.get(\"bookings\", [])` not `data.get(\"data\", {}).get(\"bookings\", [])`.",
    45: "**`import X as Y` aliasing** — `import urllib.request as _urllib` means `_urllib` IS the module. Call `_urllib.urlopen()` not `_urllib.request.urlopen()`.",
    46: "**Never duplicate financial calculation logic** — two endpoints, two different results (KBZ Bank: -30.2M vs -27.8M). Shared function eliminates divergence. Financial numbers must ALWAYS come from a single source of truth.",
}

# Replace the CRITICAL LESSONS section
old_cl_section = r"""## 🧠 Critical Lessons Learned \(Cumulative\)

### Python Patterns
### API & Database Patterns
### System Patterns
### Business Logic
33\. \*\*Charges are outgoing-only bank fees\*\* — Buy/Payable has charges \(we send money\); Sell/Receivable has NO charges \(customer pays us\)\.
34\. \*\*Never include cleanup in test scripts\*\* — caused 2 accidental data deletions; use backup restore instead\.
35\. \*\*Save-and-restore dropdown selections\*\* — when rebuilding select options via `innerHTML`, save `\.value` first then restore after\."""

new_cl_section = """## 🧠 Critical Lessons Learned (Cumulative)

### Python Patterns
### API & Database Patterns
### System Patterns
### Business Logic
44. **`unwrap_response()` changes response structure** — Functions consuming API responses must NOT access `.data` again after unwrap. Use `data.get("bookings", [])` not `data.get("data", {}).get("bookings", [])`.
45. **`import X as Y` aliasing** — `import urllib.request as _urllib` means `_urllib` IS the module. Call `_urllib.urlopen()` not `_urllib.request.urlopen()`.
46. **Never duplicate financial calculation logic** — two endpoints, two different results (KBZ Bank: -30.2M vs -27.8M). Shared function eliminates divergence. Financial numbers must ALWAYS come from a single source of truth."""

content = re.sub(old_cl_section, new_cl_section, content, count=1)
print(f"[2] Replaced CRITICAL LESSONS with 3 most recent (#44-46)")

# --- 3. FIX HISTORY: keep only 5 most recent fixes ---
# The major fix sections are in June 23 (fixes #3-#7, #11-#16) and June 27 (Other Fixes)
# Keep the 5 most recent: all from Jun 27 "Other Fixes" section

# Remove the massive "🆕 June 23, 2026 — Major Bug Fixes & Features" section 
# (keep the section header line but collapse content)
old_jun23_block_start = "## 🆕 June 23, 2026 — Major Bug Fixes & Features"
old_jun23_block_end = "## Memory (2026-06-23)"

idx_start = content.find(old_jun23_block_start)
idx_end = content.find(old_jun23_block_end)

if idx_start > 0 and idx_end > idx_start:
    # Keep just a summary line
    summary = "## 🆕 June 23, 2026 — Major Bug Fixes & Features\n\n*(10+ fixes condensed — see git for full details. Key: food_cart_release stock_out fix, Move API start_time preservation, End Session confirm step, game_amt for booking_id paths, receipt template v3, Session Reminder 3-type fix, console_mgmt imports, Move Console menu layout.)*\n\n"
    content = content[:idx_start] + summary + content[idx_end:]
    print(f"[3] Condensed June 23 Major Bug Fixes section")

# Also condense the detailed numbered fixes under Memory (2026-06-23) 
# (keep only a compact summary)
old_jun23_detail_start = "### 11. console_mgmt.py — Missing Import Fix"
old_jun23_detail_end = "## Memory (2026-06-25)"

idx_start2 = content.find(old_jun23_detail_start)
idx_end2 = content.find(old_jun23_detail_end)

if idx_start2 > 0 and idx_end2 > idx_start2:
    summary2 = "### Key Technical Notes *(fixes #11-16 condensed)*\n"
    content = content[:idx_start2] + summary2 + content[idx_end2:]
    print(f"[4] Condensed June 23 detailed fixes #11-16")

# Write back
with open(path, "w") as f:
    f.write(content)

new_size = len(content.encode())
print(f"\nOld size: {orig_size} bytes → New size: {new_size} bytes (saved {orig_size - new_size})")
print("OK" if new_size <= 22000 else f"STILL OVER LIMIT by {new_size - 22000} bytes")
