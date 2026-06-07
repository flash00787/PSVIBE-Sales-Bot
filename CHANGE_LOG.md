
## 2026-06-07 — SSD/Console Classification Fix

### Changes
- **File:** `bot/handlers/games.py`
- **What:** Fixed `_show_game_detail` and inline handler to properly separate SSD drives from Console entries
- **Root cause:** `if status == "Installed"` caught SSD entries (SSD-T1, SSD-Grey, SSD-Blue) because they all have `status="Installed"` with `install_type="Moved"/"SSD Copy"`. They were incorrectly shown under 📀 Console instead of 💾 SSD.
- **Fix:** Added `cid.upper().startswith("SSD")` check within the `status == "Installed"` branch — SSD entries now go to `ssd_list` with install_type shown.
- **Services restarted:** `psvibe-sale-bot`
- **Author:** Kora

## 2026-06-07 — SSD/Console Classification Fix

### Changes
- File: bot/handlers/games.py
- What: Fixed _show_game_detail and inline handler to separate SSD drives from Console entries
- Root cause: SSD entries (SSD-T1, SSD-Grey, SSD-Blue) have status=Installed so they went to Console list
- Fix: Added cid.upper().startswith(SSD) check — SSD entries now go to ssd_list
- Services restarted: psvibe-sale-bot
- Author: Kora

