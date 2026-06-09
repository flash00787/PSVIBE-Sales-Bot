#!/usr/bin/env python3
"""
Transform bot/__init__.py: Remove all GSheet fallbacks, make functions API-only.
Phase 2 of MySQL migration.
"""
import re
import sys

def transform(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # ──────────────────────────────────────────────────
    # STEP 0: Save original length for diff
    # ──────────────────────────────────────────────────
    original = content
    original_lines = content.split('\n')
    
    changes = []
    
    # ═══════════════════════════════════════════════════
    # STEP 1: Remove gspread imports
    # ═══════════════════════════════════════════════════
    
    # Remove 'import gspread' line
    content = re.sub(r'^import gspread\s*\n', '', content, flags=re.MULTILINE)
    if 'import gspread' in content:
        changes.append("WARNING: 'import gspread' still in file after removal attempt")
    else:
        changes.append("✓ Removed 'import gspread'")
    
    # Remove 'from gspread.exceptions import APIError'
    content = re.sub(r'^from gspread\.exceptions import APIError\s*\n', '', content, flags=re.MULTILINE)
    if 'from gspread.exceptions' in content:
        changes.append("WARNING: gspread.exceptions still referenced")
    else:
        changes.append("✓ Removed gspread.exceptions import")
    
    # Remove 'from oauth2client.service_account import ServiceAccountCredentials'
    content = re.sub(r'^from oauth2client\.service_account import ServiceAccountCredentials\s*\n', '', content, flags=re.MULTILINE)
    if 'oauth2client' in content and 'ServiceAccountCredentials' in content:
        changes.append("WARNING: oauth2client still referenced")
    else:
        changes.append("✓ Removed oauth2client import")
    
    # Remove the gspread retry wrapper block (lines between # GOOGLE SHEETS RETRY WRAPPER and next major section)
    # This block spans from "# ─────────────────────────────────────────" through "_sheets_retry" function
    retry_block_start = content.find("# ─────────────────────────────────────────\n#  GOOGLE SHEETS RETRY WRAPPER")
    if retry_block_start >= 0:
        # Find the end of the _sheets_retry wrapper function (it ends with "return wrapper")
        # Then find the next non-blank line after it
        wrapper_end = content.find("\n    return wrapper\n", retry_block_start)
        if wrapper_end >= 0:
            wrapper_end += len("\n    return wrapper\n")
            # Skip any trailing blank lines
            while wrapper_end < len(content) and content[wrapper_end] == '\n':
                wrapper_end += 1
            content = content[:retry_block_start] + content[wrapper_end:]
            changes.append("✓ Removed GSheet retry wrapper")
        else:
            changes.append("WARNING: Could not find end of retry wrapper")

    # Remove _gsheets_executor, _SHEETS_RETRY_CODES etc
    for var in ['_gsheets_executor', '_SHEETS_RETRY_CODES', '_SHEETS_MAX_RETRIES', '_SHEETS_BASE_DELAY']:
        content = re.sub(rf'^{var}\s*=\s*[^\n]+\n', '', content, flags=re.MULTILINE)
    
    # Remove SheetsPermissionError class
    content = re.sub(
        r'^class SheetsPermissionError\(Exception\):.*?(?=\n(def |class |[A-Z_]+ = |$))',
        '', content, flags=re.MULTILINE|re.DOTALL
    )
    
    # Remove _get_sa_email function
    content = re.sub(
        r"^def _get_sa_email\(sa_file: str = \"service_account\.json\"\) -> str:.*?(?=\n(def |class |[A-Z_]+ = |import |from |$))",
        '', content, flags=re.MULTILINE|re.DOTALL
    )
    
    # Remove _sheets_retry function (if not removed by block above)
    content = re.sub(
        r'^def _sheets_retry\(func\):.*?(?=\n(def |class |[A-Z_]+ = |import |from |from oauth|$))',
        '', content, flags=re.MULTILINE|re.DOTALL
    )
    
    # Remove gspread ThreadPoolExecutor line - the _gsheets_executor = concurrent.futures... line
    # Already handled above by variable removal
    
    # Remove `import functools` and `import concurrent.futures` if only used by gspread
    # Actually let's keep them, they might be used elsewhere.
    
    changes.append("✓ Cleaned up gspread infrastructure imports/code")
    
    # ═══════════════════════════════════════════════════
    # STEP 2: Transform all functions with API+fallback pattern
    # ═══════════════════════════════════════════════════
    
    # We need to find all blocks that have:
    #   if _HAS_API:
    #       result = api_xxx(...)
    #       if result is not None:
    #           ... = result.get(...)
    #           return ...
    #       logging.warning("API ... failed, falling back to gspread")
    #   # gspread fallback code follows
    #
    # For each such block, we convert to:
    #   result = api_xxx(...)
    #   if result is not None:
    #       ... = result.get(...)
    #       return ...
    #   logging.error("API ... failed")
    #   return default_value
    
    content = transform_fetch_console_status(content, changes)
    content = transform_create_booking(content, changes)
    content = transform_end_booking(content, changes)
    content = transform_fetch_games(content, changes)
    content = transform_set_game_disc_count(content, changes)
    content = transform_fetch_console_games(content, changes)
    content = transform_get_games_on_console(content, changes)
    content = transform_get_consoles_with_game(content, changes)
    content = transform_add_console_game(content, changes)
    content = transform_remove_console_game(content, changes)
    content = transform_update_game_library_install(content, changes)
    content = transform_cancel_booking(content, changes)
    content = transform_add_console_to_setting(content, changes)
    content = transform_remove_console_from_setting(content, changes)
    content = transform_update_console_multiplier(content, changes)
    content = transform_next_voucher(content, changes)
    content = transform_fetch_members(content, changes)
    content = transform_fetch_members_async(content, changes)
    content = transform_fetch_attendance(content, changes)
    content = transform_save_attendance(content, changes)
    content = transform_fetch_staff(content, changes)
    content = transform_fetch_base_salaries(content, changes)
    content = transform_fetch_promotions_cached(content, changes)
    content = transform_fetch_allowed_staff_ids(content, changes)
    content = transform_fetch_allowed_staff_ids_async(content, changes)
    content = transform_fetch_wallet_mins(content, changes)
    content = transform_fetch_wallet_mins_async(content, changes)
    content = transform_fetch_base_rate(content, changes)
    content = transform_fetch_base_rate_async(content, changes)
    content = transform_fetch_new_member_defaults(content, changes)
    content = transform_fetch_food_prices(content, changes)
    content = transform_fetch_food_prices_async(content, changes)
    content = transform_fetch_food_costs(content, changes)
    content = transform_fetch_food_costs_async(content, changes)
    content = transform_fetch_console_multiplier(content, changes)
    content = transform_fetch_console_multiplier_async(content, changes)
    content = transform_fetch_rank_thresholds(content, changes)
    content = transform_fetch_member_data_1(content, changes)  # line 2511
    content = transform_fetch_member_data_2(content, changes)  # line 2527
    content = transform_fetch_member_data_3(content, changes)  # line 2546
    content = transform_fetch_member_data_4(content, changes)  # line 2690
    content = transform_fetch_referral_code(content, changes)
    content = transform_fetch_balance_mins(content, changes)
    content = transform_fetch_member_effective_rate(content, changes)
    content = transform_build_member_rate_dict(content, changes)
    content = transform_fetch_member_tier(content, changes)
    content = transform_fetch_bonus_table(content, changes)
    content = transform_next_member_row_no(content, changes)
    content = transform_next_member_id(content, changes)
    content = transform_fetch_rank_table_display(content, changes)
    
    # Also remove "falling back to gspread" log lines that might remain
    # Find any remaining lines with "falling back to gspread" 
    remaining = content.count("falling back to gspread")
    if remaining > 0:
        # Replace remaining "falling back" with "API unavailable, returning default"
        content = content.replace(
            'logging.warning("API api_fetch_console_status() failed, falling back to gspread")',
            'logging.error("API api_fetch_console_status() failed")'
        )
        content = content.replace(
            'logging.warning("API api_fetch_game_library() failed, falling back to gspread")',
            'logging.error("API api_fetch_game_library() failed")'
        )
        content = content.replace(
            'logging.warning("API api_fetch_console_games() failed, falling back to gspread")',
            'logging.error("API api_fetch_console_games() failed")'
        )
        changes.append(f"⚠ Still {content.count('falling back to gspread')} 'falling back' lines remain after all transforms")
    
    # Remove now-unused imports that were only for gspread
    # Actually let's handle this carefully - functools and concurrent.futures might still be needed
    
    # ═══════════════════════════════════════════════════
    # STEP 3: Remove wb-related getter functions that create sheets
    # ═══════════════════════════════════════════════════
    
    # remove get_salary_adv_sh, get_game_lib_sh, get_console_games_sh, get_booking_sh, 
    # get_att_sh, setting_sh references, ensure_sheet_headers
    # BUT these might be called from gspread fallback code we're removing
    # Let's check after transforms
    
    return content, changes


# ──────────────────────────────────────────────
# Individual function transformers
# ──────────────────────────────────────────────

def _find_fn_block(content, fn_name, after_pos=0):
    """Find the start of a function definition. Returns start, end positions or (None, None)."""
    idx = content.find(f"def {fn_name}(", after_pos)
    if idx < 0:
        return None, None
    return idx, None  # We'll find the end in each transformer

def _find_next_def(content, pos):
    """Find the next 'def ' or end of file."""
    # Find next def at the same indentation level
    next_def = content.find("\ndef ", pos + 1)
    if next_def < 0:
        return len(content)
    return next_def + 1  # include newline

def _extract_function(content, fn_name, after_pos=0):
    """Extract full function text. Returns (start_pos, end_pos, text) or (None, None, None)."""
    start = content.find(f"def {fn_name}(", after_pos)
    if start < 0:
        return None, None, None
    
    # Find end: next def at top level (no indent before 'def')
    # Look for \ndef with no leading whitespace before it
    pos = start
    while True:
        next_def = content.find("\ndef ", pos + 1)
        if next_def < 0:
            return start, len(content), content[start:]
        # Check if this def is at top level (no indent)
        line_start = content.rfind('\n', 0, next_def) + 1
        if content[line_start:next_def + 5].startswith("def "):
            return start, next_def, content[start:next_def]
        # Also check for class definitions
        next_class = content.find("\nclass ", pos + 1)
        if next_class >= 0 and next_class < next_def:
            line_start = content.rfind('\n', 0, next_class) + 1
            if content[line_start:next_class + 7].startswith("class "):
                return start, next_class, content[start:next_class]
        pos = next_def

    return start, len(content), content[start:]


def _remove_if_has_api_block(text, api_var, api_func, return_value_on_fail, logging_warning_pattern=None):
    """
    Transform:
        if _HAS_API:
            result = api_func(...)
            if result is not None:
                ...process...
                return x
            logging.warning("API ... failed, falling back to gspread")
        ...gspread fallback code...
    
    Into:
        result = api_func(...)
        if result is not None:
            ...process...
            return x
        logging.error("API ... failed")
        return return_value_on_fail
    
    Returns (new_text, changed_bool)
    """
    if f"if _HAS_API:" not in text:
        return text, False
    
    # Find the if _HAS_API: block
    if_idx = text.find("if _HAS_API:")
    if if_idx < 0:
        return text, False
    
    # Find indentation level
    indent = text[:if_idx]  # should be just whitespace
    inner_indent = indent + "    "  # 4 more spaces for content inside if
    
    # Find "falling back to gspread" line
    fallback_idx = text.find("falling back to gspread", if_idx)
    if fallback_idx < 0:
        return text, False
    
    # Find the end of the warning line
    warn_line_end = text.find('\n', fallback_idx)
    if warn_line_end < 0:
        warn_line_end = len(text)
    
    # Find where the gspread fallback code starts (after the if _HAS_API: block)
    # The block structure is:
    #         if _HAS_API:
    #             result = api_xxx(...)
    #             if result is not None:
    #                 ...  (possibly multiple lines)
    #             logging.warning("...falling back...")
    #     ...gspread fallback code...
    #
    # We need to find the line after the warning log that is at a LESSER indent
    # (the gspread fallback code that was outside the if _HAS_API block)
    
    # Find where the IF block ends: look for first line after fallback that has same or less indent than `if _HAS_API:`
    after_warn = warn_line_end + 1
    gspread_start = after_warn
    
    # Find the line that's at the SAME indent level as `if _HAS_API:` (or less)
    lines = text[if_idx:].split('\n')
    if_block_lines = []
    gspread_lines = []
    in_if_block = True
    found_fallback = False
    
    for i, line in enumerate(lines):
        if i == 0:  # "if _HAS_API:"
            if_block_lines.append(line)
            continue
        if not found_fallback:
            if "falling back to gspread" in line:
                found_fallback = True
                if_block_lines.append(line)
                continue
            if_block_lines.append(line)
        else:
            # We're past the fallback warning
            stripped = line.lstrip()
            if stripped and not line.startswith(indent + " "):
                # This line has less indent than the if block content
                # It's the gspread fallback code
                gspread_lines.append(line)
            elif stripped:
                # Still has same or more indent - part of if block (but should not happen after fallback)
                # Check if this is the beginning of gspread fallback code at if indent level
                if line.startswith(indent) and not line.startswith(indent + " "):
                    gspread_lines.append(line)
                else:
                    if_block_lines.append(line)
            else:
                # empty line - could be either, add to where we are
                gspread_lines.append(line)
    
    if not gspread_lines:
        return text, False
    
    # Now rebuild:
    # 1. Remove "if _HAS_API:" from first line
    # 2. Un-indent the if block lines by 4 spaces
    # 3. Replace "falling back to gspread" with "failed"
    # 4. Add error log + return default at the end
    # 5. Drop the gspread fallback lines
    
    new_lines = []
    
    # Process if block lines
    for i, line in enumerate(if_block_lines):
        if i == 0:
            # Skip the "if _HAS_API:" line entirely
            continue
        # Remove one level of indent (4 spaces)
        if line.startswith(inner_indent):
            line = line[len(inner_indent):]
        elif line.startswith(indent):
            line = line[len(indent):]
        new_lines.append(line)
    
    # Find the last non-empty line
    while new_lines and new_lines[-1].strip() == '':
        new_lines.pop()
    
    # Replace the fallback warning with error
    for i, line in enumerate(new_lines):
        if "falling back to gspread" in line:
            # Replace logging.warning with logging.error and remove fallback message
            new_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_lines[i] = new_lines[i].replace('failed, falling back to gspread")', 'failed")')
            new_lines[i] = new_lines[i].replace('returned empty data, falling back to gspread")', 'returned empty data")')
            new_lines[i] = new_lines[i].replace('returned success=False, falling back to gspread")', 'returned success=False")')
            break
    
    # Check if the last real line is already a return statement
    # If not, add a return with default value
    has_return = False
    for line in reversed(new_lines):
        stripped = line.strip()
        if stripped.startswith('return '):
            has_return = True
            break
        if stripped and not stripped.startswith('#'):
            break
    
    if not has_return and return_value_on_fail is not None:
        # Add return with default before removing trailing blanks
        if return_value_on_fail in ('True', 'False'):
            new_lines.append(f"    return {return_value_on_fail}")
        elif return_value_on_fail in ('[]', '{}', '""', "''"):
            new_lines.append(f"    return {return_value_on_fail}")
        else:
            new_lines.append(f"    return {return_value_on_fail}")
    
    # Reconstruct: prefix, new_lines, suffix (everything after gspread code)
    prefix = text[:if_idx]
    suffix_start = if_idx + len('\n'.join(lines))
    suffix = text[suffix_start:]
    
    result = prefix + '\n'.join(new_lines) + suffix
    return result, True


# ── Generic transformation helper ──

def _transform_fn_simple(content, fn_name, return_default, changes_label, start_after=0):
    """Simple transformation: extract function, apply _remove_if_has_api_block, replace."""
    start, end, fn_text = _extract_function(content, fn_name, start_after)
    if fn_text is None:
        changes.append(f"⚠ Function {fn_name} not found")
        return content
    
    new_text, changed = _remove_if_has_api_block(fn_text, None, None, return_default)
    if changed:
        content = content[:start] + new_text + content[end:]
        changes.append(f"✓ Transformed {fn_name} ({changes_label})")
    else:
        changes.append(f"⚠ No change needed for {fn_name}")
    return content


# ─────────────────────────────────────────────────
# Individual transforms
# ─────────────────────────────────────────────────

def transform_fetch_console_status(content, changes):
    """Transform fetch_console_status() - has a complex pattern with settings_config fallback."""
    start, end, fn_text = _extract_function(content, "fetch_console_status")
    if fn_text is None:
        changes.append("⚠ fetch_console_status not found")
        return content
    
    # This function has:
    #     if _HAS_API:
    #         result = api_fetch_console_status()
    #         if result is not None:
    #             ...mapping code...
    #             return deduped
    #         logging.warning("API api_fetch_console_status() failed, falling back to gspread")
    #     [gspread code: today = today_str(), setting_sh, etc.]
    #     [overlay active bookings from get_booking_sh()...]
    #     return consoles
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    # Find the if _HAS_API block
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    
    # Find the fallback warning line
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    # The API block lines (indented under if _HAS_API:)
    api_block = fn_text[api_if_start:warn_line_end + 1]
    # Remaining gspread code
    gspread_part = fn_text[warn_line_end + 1:]
    
    # Transform API block: remove "if _HAS_API:" line, unindent by 4 spaces
    api_lines = api_block.split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):  # 8 spaces
            new_api_lines.append(line[4:])  # Reduce to 4 spaces (function body indent)
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    # Replace warning with error
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    # Add return [] at the end of API block (in case API returns None)
    # But check if there's already a return before that
    has_return = any('return ' in l.strip() and not l.strip().startswith('#') for l in new_api_lines)
    if not has_return:
        new_api_lines.append("    return []")
    
    # Add comment to replace gspread code
    replacement = before_if + '\n'.join(new_api_lines) + '\n    # GSheet fallback removed — MySQL API is the single source of truth\n    return []\n'
    
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed fetch_console_status (console status)")
    return content


def transform_create_booking(content, changes):
    start, end, fn_text = _extract_function(content, "create_booking")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    # Pattern:
    #     if _HAS_API:
    #         result = api_create_booking(...)
    #         if result is not None:
    #             bk = result.get("data", {}).get("booking_id") or ""
    #             if bk:
    #                 return bk
    #         logging.warning("API api_create_booking() failed, falling back to gspread")
    #     sh = get_booking_sh()
    #     ...gspread code...
    #     return bk_id
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_block = fn_text[api_if_start:warn_line_end + 1]
    
    # Transform API block
    api_lines = api_block.split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    # Add error return if not present
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    logging.error(f"API api_create_booking() failed for {console_id}, {member_id}")')
        new_api_lines.append('    return ""')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed create_booking")
    return content


def transform_end_booking(content, changes):
    start, end, fn_text = _extract_function(content, "end_booking")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return False')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed end_booking")
    return content


def transform_fetch_games(content, changes):
    start, end, fn_text = _extract_function(content, "fetch_games")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return []')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed fetch_games")
    return content


def transform_set_game_disc_count(content, changes):
    start, end, fn_text = _extract_function(content, "set_game_disc_count")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return False')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed set_game_disc_count")
    return content


def transform_fetch_console_games(content, changes):
    start, end, fn_text = _extract_function(content, "fetch_console_games")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return []')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed fetch_console_games")
    return content


def transform_get_games_on_console(content, changes):
    start, end, fn_text = _extract_function(content, "get_games_on_console")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return []')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed get_games_on_console")
    return content


def transform_get_consoles_with_game(content, changes):
    start, end, fn_text = _extract_function(content, "get_consoles_with_game")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return []')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed get_consoles_with_game")
    return content


def transform_add_console_game(content, changes):
    start, end, fn_text = _extract_function(content, "add_console_game")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return False')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed add_console_game")
    return content


def transform_remove_console_game(content, changes):
    start, end, fn_text = _extract_function(content, "remove_console_game")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return False')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed remove_console_game")
    return content


def transform_update_game_library_install(content, changes):
    start, end, fn_text = _extract_function(content, "update_game_library_install")
    if fn_text is None:
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines = fn_text[api_if_start:warn_line_end + 1].split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        new_api_lines.append('    return False')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append("✓ Transformed update_game_library_install")
    return content


def _transform_simple_fn(content, fn_name, return_val, changes):
    """Generic transform for a simple function with if _HAS_API: → fallback pattern."""
    start, end, fn_text = _extract_function(content, fn_name)
    if fn_text is None:
        changes.append(f"⚠ {fn_name} not found")
        return content
    
    if "if _HAS_API:" not in fn_text:
        changes.append(f"⚠ {fn_name} has no if _HAS_API: block")
        return content
    
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    
    if warn_idx < 0:
        changes.append(f"⚠ {fn_name} has _HAS_API but no 'falling back' message")
        return content
    
    warn_line_end = fn_text.find('\n', warn_idx)
    
    api_lines_text = fn_text[api_if_start:warn_line_end + 1]
    api_lines = api_lines_text.split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
            new_api_lines[i] = new_api_lines[i].replace('returned empty data, falling back to gspread")', 'returned empty data")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        if return_val in ['True', 'False']:
            new_api_lines.append(f'    return {return_val}')
        elif return_val in ['[]', '{}', '""', "''", 'None', '0', '""']:
            new_api_lines.append(f'    return {return_val}')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append(f"✓ Transformed {fn_name}")
    return content


def transform_cancel_booking(content, changes):
    return _transform_simple_fn(content, "cancel_booking", "False", changes)

def transform_add_console_to_setting(content, changes):
    return _transform_simple_fn(content, "add_console_to_setting", "False", changes)

def transform_remove_console_from_setting(content, changes):
    return _transform_simple_fn(content, "remove_console_from_setting", "False", changes)

def transform_update_console_multiplier(content, changes):
    return _transform_simple_fn(content, "update_console_multiplier", "False", changes)

def transform_next_voucher(content, changes):
    return _transform_simple_fn(content, "next_voucher", '""', changes)

def transform_fetch_members(content, changes):
    return _transform_simple_fn(content, "fetch_members", "[]", changes)

def transform_fetch_members_async(content, changes):
    return _transform_simple_fn(content, "fetch_members_async", "{}", changes)

def transform_fetch_attendance(content, changes):
    return _transform_simple_fn(content, "fetch_attendance", "[]", changes)

def transform_save_attendance(content, changes):
    return _transform_simple_fn(content, "save_attendance", "False", changes)

def transform_fetch_staff(content, changes):
    return _transform_simple_fn(content, "fetch_staff", "[]", changes)

def transform_fetch_base_salaries(content, changes):
    return _transform_simple_fn(content, "fetch_base_salaries", "{}", changes)

def transform_fetch_promotions_cached(content, changes):
    return _transform_simple_fn(content, "fetch_promotions_cached", "[]", changes)

def transform_fetch_allowed_staff_ids(content, changes):
    return _transform_simple_fn(content, "fetch_allowed_staff_ids", "[]", changes)

def transform_fetch_allowed_staff_ids_async(content, changes):
    return _transform_simple_fn(content, "fetch_allowed_staff_ids_async", "{}", changes)

def transform_fetch_wallet_mins(content, changes):
    return _transform_simple_fn(content, "fetch_wallet_mins", "{}", changes)

def transform_fetch_wallet_mins_async(content, changes):
    return _transform_simple_fn(content, "fetch_wallet_mins_async", "{}", changes)

def transform_fetch_base_rate(content, changes):
    return _transform_simple_fn(content, "fetch_base_rate", "0", changes)

def transform_fetch_base_rate_async(content, changes):
    return _transform_simple_fn(content, "fetch_base_rate_async", "{}", changes)

def transform_fetch_new_member_defaults(content, changes):
    return _transform_simple_fn(content, "fetch_new_member_defaults", "{}", changes)

def transform_fetch_food_prices(content, changes):
    return _transform_simple_fn(content, "fetch_food_prices", "[]", changes)

def transform_fetch_food_prices_async(content, changes):
    return _transform_simple_fn(content, "fetch_food_prices_async", "{}", changes)

def transform_fetch_food_costs(content, changes):
    return _transform_simple_fn(content, "fetch_food_costs", "[]", changes)

def transform_fetch_food_costs_async(content, changes):
    return _transform_simple_fn(content, "fetch_food_costs_async", "{}", changes)

def transform_fetch_console_multiplier(content, changes):
    return _transform_simple_fn(content, "fetch_console_multiplier", "{}", changes)

def transform_fetch_console_multiplier_async(content, changes):
    return _transform_simple_fn(content, "fetch_console_multiplier_async", "{}", changes)

def transform_fetch_rank_thresholds(content, changes):
    return _transform_simple_fn(content, "fetch_rank_thresholds", "{}", changes)

def transform_fetch_member_data_1(content, changes):
    # There are 4 fetch_member_data functions/locations. 
    # Use _extract_function with start_after to find the right one.
    
    # Find first occurrence
    start, end, fn_text = _extract_function(content, "fetch_member_data")
    if fn_text is None:
        changes.append("⚠ fetch_member_data#1 not found")
        return content
    
    if "if _HAS_API:" not in fn_text:
        changes.append("⚠ fetch_member_data#1 has no _HAS_API")
        return content
    
    content = _transform_simple_fn_internal(content, start, end, fn_text, "fetch_member_data", "{}", changes)
    return content

def transform_fetch_member_data_2(content, changes):
    # Find second occurrence after the first one was already transformed
    start, end, fn_text = _extract_function(content, "fetch_member_data")
    if fn_text is None:
        changes.append("⚠ fetch_member_data#2 not found")
        return content
    
    if "if _HAS_API:" not in fn_text:
        # Could be the already-transformed one. Try again.
        return content
    
    content = _transform_simple_fn_internal(content, start, end, fn_text, "fetch_member_data#2", "{}", changes)
    return content

def transform_fetch_member_data_3(content, changes):
    start, end, fn_text = _extract_function(content, "fetch_member_data")
    if fn_text is None:
        changes.append("⚠ fetch_member_data#3 not found")
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    content = _transform_simple_fn_internal(content, start, end, fn_text, "fetch_member_data#3", "{}", changes)
    return content

def transform_fetch_member_data_4(content, changes):
    start, end, fn_text = _extract_function(content, "fetch_member_data")
    if fn_text is None:
        changes.append("⚠ fetch_member_data#4 not found")
        return content
    
    if "if _HAS_API:" not in fn_text:
        return content
    
    content = _transform_simple_fn_internal(content, start, end, fn_text, "fetch_member_data#4", "{}", changes)
    return content

def _transform_simple_fn_internal(content, start, end, fn_text, label, return_val, changes):
    """Internal helper: transform a single function text block."""
    api_if_start = fn_text.find("if _HAS_API:")
    before_if = fn_text[:api_if_start]
    warn_idx = fn_text.find("falling back to gspread", api_if_start)
    
    if warn_idx < 0:
        changes.append(f"⚠ {label} has _HAS_API but no 'falling back'")
        return content
    
    warn_line_end = fn_text.find('\n', warn_idx)
    api_lines_text = fn_text[api_if_start:warn_line_end + 1]
    api_lines = api_lines_text.split('\n')
    new_api_lines = []
    for line in api_lines:
        if line.strip() == "if _HAS_API:":
            continue
        if line.startswith("        "):
            new_api_lines.append(line[4:])
        elif line.startswith("    "):
            new_api_lines.append(line)
        else:
            new_api_lines.append(line)
    
    for i, line in enumerate(new_api_lines):
        if "falling back to gspread" in line:
            new_api_lines[i] = line.replace('logging.warning("', 'logging.error("')
            new_api_lines[i] = new_api_lines[i].replace('failed, falling back to gspread")', 'failed")')
            new_api_lines[i] = new_api_lines[i].replace('returned empty data, falling back to gspread")', 'returned empty data")')
    
    has_return = any('return ' in l.strip() for l in new_api_lines if l.strip())
    if not has_return:
        if return_val in ['True', 'False']:
            new_api_lines.append(f'    return {return_val}')
        elif return_val in ['[]', '{}', '""', "''", 'None', '0', '""']:
            new_api_lines.append(f'    return {return_val}')
    
    replacement = before_if + '\n'.join(new_api_lines) + '\n'
    content = content[:start] + replacement + content[end:]
    changes.append(f"✓ Transformed {label}")
    return content


def transform_fetch_referral_code(content, changes):
    return _transform_simple_fn(content, "fetch_referral_code", "{}", changes)

def transform_fetch_balance_mins(content, changes):
    return _transform_simple_fn(content, "fetch_balance_mins", "{}", changes)

def transform_fetch_member_effective_rate(content, changes):
    return _transform_simple_fn(content, "fetch_member_effective_rate", "{}", changes)

def transform_build_member_rate_dict(content, changes):
    return _transform_simple_fn(content, "build_member_rate_dict", "{}", changes)

def transform_fetch_member_tier(content, changes):
    return _transform_simple_fn(content, "fetch_member_tier", "{}", changes)

def transform_fetch_bonus_table(content, changes):
    return _transform_simple_fn(content, "fetch_bonus_table", "{}", changes)

def transform_next_member_row_no(content, changes):
    return _transform_simple_fn(content, "next_member_row_no", "0", changes)

def transform_next_member_id(content, changes):
    return _transform_simple_fn(content, "next_member_id", '""', changes)

def transform_fetch_rank_table_display(content, changes):
    return _transform_simple_fn(content, "fetch_rank_table_display", "[]", changes)


# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else '/home/node/.openclaw/workspace/temp_init_py.txt'
    output_path = sys.argv[2] if len(sys.argv) > 2 else filepath + '.transformed'
    
    content, changes = transform(filepath)
    
    # Print changes
    for c in changes:
        print(c)
    
    # Write output
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"\nOutput written to {output_path}")
    print(f"Original: {len(open(filepath).read())} chars")
    print(f"Modified: {len(content)} chars")
    
    # Final check
    remaining = content.count("falling back to gspread")
    print(f"Remaining 'falling back to gspread': {remaining}")
