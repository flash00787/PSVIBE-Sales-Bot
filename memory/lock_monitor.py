#!/usr/bin/env python3
"""
lock_monitor.py — Automatic stale lock detection and cleanup.
Prevents agent deadlocks by removing orphaned lock files.

Checks:
  1. Session lock files (.jsonl.lock) in gateway session dir
  2. Code file locks (lock_manager.py)
  3. Fix locks (fix_lock.py)
  4. Old session/topic files (>SESSION_MAX_AGE_DAYS)
  5. Oversized trajectory files
  6. Trajectory & checkpoint auto-cleanup (now cleans, not just warns)
  7. Session bloat auto-clean (>500KB + old)
  8. Total disk usage summary

Heuristic:
  - PID dead → immediate cleanup
  - PID alive + lock age > STALE_AFTER_SECS → cleanup (deadlock/orphan)
  - PID alive + lock age > maxHoldMs → cleanup (stale even if pid alive)
  - PID alive + lock age < STALE_AFTER_SECS → keep (active lock)

Usage:
  python3 /root/coordination/lock_monitor.py --once       # One-shot (for cron)
  python3 /root/coordination/lock_monitor.py --status      # Show current state
  python3 /root/coordination/lock_monitor.py --dry-run --once  # Preview without deleting
  python3 /root/coordination/lock_monitor.py --daemon      # Continuous (optional)
"""

import os
import sys
import json
import time
import glob
import subprocess

# ── Config ──
STALE_AFTER_SECS = 45  # 45s — locks older than this with dead/mismatched PID = deadlock
SAME_PID_STALE_SECS = 300  # 5 min — only clean if same PID held lock this long (prevent corruption)
SESSION_LOCK_GLOB = "/home/node/.openclaw/agents/main/sessions/*.jsonl.lock"
SESSION_GLOB = "/home/node/.openclaw/agents/main/sessions/*.jsonl"
LOCK_MANAGER = "/root/coordination/lock_manager.py"
FIX_LOCK = "/root/coordination/fix_lock.py"
MAX_OWN_SESSIONS = 10  # keep last N lock monitor sessions, delete the rest
SESSION_SIZE_WARN_KB = 500  # warn if main topic session > 500KB (>200 msgs → write timeout risk)
SESSION_MAX_AGE_DAYS = 2  # delete session files older than this (was 7 — too long; files bloat to 10MB in 2 days)
TRAJECTORY_MAX_SIZE_KB = 3000  # warn if trajectory files > 3MB (was 5MB — reduced to catch earlier)
TRAJECTORY_MAX_AGE_DAYS = 2  # delete trajectory .jsonl files older than this (was 7 — too long)
CHECKPOINT_MAX_AGE_DAYS = 2  # delete checkpoint .jsonl files older than this (was 7 — too long)
TRAJECTORY_FORCE_CLEAN_KB = 10000  # force-clean trajectory files >10MB regardless of age (prevents lock timeouts)

# ── Globals ──
DRY_RUN = False
_total_locks_cleaned = 0
_total_files_removed = 0
_total_freed_kb = 0.0
_total_warnings = 0


def _is_pid_alive(pid):
    """Check if a PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, PermissionError, ProcessLookupError):
        return False


def _is_same_process(pid, expected_starttime):
    """Check if the current process with given PID is the same instance (starttime matches)."""
    if expected_starttime <= 0:
        return False
    try:
        # Read /proc/<pid>/stat — field 22 is starttime (after ')', 1-indexed from there)
        with open(f"/proc/{pid}/stat") as f:
            stat = f.read()
        # Find the closing ')' to skip the comm field
        close_paren = stat.rfind(')')
        fields = stat[close_paren + 2:].split()
        # Field index: after ')' + space, starttime is the 20th field (0-indexed: 19)
        current_starttime = int(fields[19])
        return current_starttime == expected_starttime
    except (IOError, OSError, IndexError, ValueError):
        return False


def _parse_iso_ts(ts):
    """Parse ISO 8601 timestamp to epoch seconds."""
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        from datetime import datetime
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0


def _remove_file(path, size=0):
    """Delete a file, respecting DRY_RUN. Returns (removed, freed_kb)."""
    global DRY_RUN, _total_files_removed, _total_freed_kb
    if DRY_RUN:
        if size <= 0:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
        print(f"  [DRY-RUN] Would remove: {os.path.basename(path)} ({size/1024:.0f}KB)")
        return 1, size / 1024
    try:
        if size <= 0:
            size = os.path.getsize(path)
        os.remove(path)
        _total_files_removed += 1
        _total_freed_kb += size / 1024
        return 1, size / 1024
    except FileNotFoundError:
        return 0, 0
    except (IOError, OSError) as e:
        global _total_warnings
        _total_warnings += 1
        print(f"  [WARN] Could not remove {os.path.basename(path)}: {e}")
        return 0, 0


def check_session_locks():
    """Check session lock files and report/clean stale ones."""
    global _total_locks_cleaned
    cleaned = 0
    active = 0
    now = time.time()
    report = []

    for lockpath in glob.glob(SESSION_LOCK_GLOB):
        try:
            with open(lockpath) as f:
                data = json.load(f)
        except FileNotFoundError:
            continue
        except (json.JSONDecodeError, IOError):
            removed, freed = _remove_file(lockpath)
            if removed:
                cleaned += 1
                _total_locks_cleaned += 1
                report.append(f"  [CLEANED] {os.path.basename(lockpath)} — corrupt")
            continue

        lock_pid = data.get("pid", 0)
        created_at = data.get("createdAt", "")
        max_hold_ms = data.get("maxHoldMs", 1020000)
        lock_starttime = data.get("starttime", 0)

        created_epoch = _parse_iso_ts(created_at)
        age_sec = now - created_epoch if created_epoch > 0 else 0

        pid_alive = _is_pid_alive(lock_pid)
        same_instance = _is_same_process(lock_pid, lock_starttime) if pid_alive else False

        # Determine if stale:
        # - PID dead: always clean
        # - PID alive, different instance (starttime mismatch → old crashed process): clean after STALE_AFTER_SECS
        # - PID alive, same instance: only clean after SAME_PID_STALE_SECS (prevent corruption)
        should_clean = False
        reason = ""

        if not pid_alive:
            should_clean = True
            reason = f"PID {lock_pid} dead, age {age_sec:.0f}s"
        elif not same_instance:
            if age_sec > STALE_AFTER_SECS:
                should_clean = True
                reason = f"PID {lock_pid} alive but different instance, stale {age_sec:.0f}s"
        else:
            if age_sec > SAME_PID_STALE_SECS:
                should_clean = True
                reason = f"Same PID {lock_pid}, stale {age_sec:.0f}s (> {SAME_PID_STALE_SECS}s)"

        if should_clean:
            removed, freed = _remove_file(lockpath)
            if removed:
                cleaned += 1
                _total_locks_cleaned += 1
            report.append(f"  [CLEANED] {os.path.basename(lockpath)} — {reason}")
        else:
            active += 1
            report.append(f"  [ACTIVE] {os.path.basename(lockpath)} — age {age_sec:.0f}s, PID {lock_pid}")

    return cleaned, active, report


def check_code_locks():
    """Check lock_manager.py and fix_lock.py for stale locks."""
    issues = []
    try:
        result = subprocess.run(
            ["python3", LOCK_MANAGER, "status"],
            capture_output=True, text=True, timeout=10
        )
        if "Active" in result.stdout and "No active" not in result.stdout:
            issues.append("  ⚠️ Code locks exist — check lock_manager.py status")
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["python3", FIX_LOCK, "status"],
            capture_output=True, text=True, timeout=10
        )
        if "active locks" in result.stdout and "no active" not in result.stdout:
            issues.append("  ⚠️ Fix locks exist — check fix_lock.py status")
    except Exception:
        pass

    return issues


def check_session_bloat():
    """Check if main session files are too large (risk of write lock timeout).
    Only checks the CURRENT main session topic (not old topics)."""
    topic_files = glob.glob(os.path.join(os.path.dirname(SESSION_GLOB), "*-topic-*.jsonl"))
    
    topics = {}
    for f in topic_files:
        fn = os.path.basename(f)
        parts = fn.split("-topic-")
        if len(parts) == 2:
            sid = parts[0]
            try:
                mtime = os.path.getmtime(f)
                if sid not in topics or mtime > topics[sid][1]:
                    topics[sid] = (fn, mtime)
            except OSError:
                continue
    
    now = time.time()
    bloat = []
    for sid, (fn, mtime) in topics.items():
        if (now - mtime) < 86400:
            fpath = os.path.join(os.path.dirname(SESSION_GLOB), fn)
            try:
                size_kb = os.path.getsize(fpath) / 1024
                if size_kb > SESSION_SIZE_WARN_KB:
                    bloat.append((fn, size_kb))
            except OSError:
                continue
    return bloat


def check_trajectory_bloat():
    """Check and warn about oversized trajectory files."""
    global _total_warnings
    warnings = []
    for f in glob.glob(os.path.join(os.path.dirname(SESSION_GLOB), "*.trajectory.jsonl")):
        try:
            size_kb = os.path.getsize(f) / 1024
            if size_kb > TRAJECTORY_MAX_SIZE_KB:
                fn = os.path.basename(f)
                warnings.append((fn, size_kb))
                _total_warnings += 1
        except OSError:
            continue
    return warnings


def cleanup_old_sessions():
    """Delete session files (.jsonl, .trajectory.jsonl, .checkpoint.*.jsonl, and .lock)
    older than SESSION_MAX_AGE_DAYS. Only cleans topic files, not active main session files."""
    global _total_warnings
    now = time.time()
    max_age_sec = SESSION_MAX_AGE_DAYS * 86400
    deleted = 0
    freed_kb = 0.0
    sessions_dir = os.path.dirname(SESSION_GLOB)
    
    for f in glob.glob(SESSION_GLOB):
        fn = os.path.basename(f)
        try:
            mtime = os.path.getmtime(f)
            age = now - mtime
            # Skip files modified in last 24h
            if age < 86400:
                continue
            # Only clean topic files (not active main sessions)
            if "topic-" not in fn:
                continue
            if age > max_age_sec:
                fsize = os.path.getsize(f)
                removed, kb = _remove_file(f, fsize)
                if removed:
                    deleted += 1
                    freed_kb += kb
                
                # Also remove companion .lock file
                lockpath = f + ".lock"
                if os.path.exists(lockpath):
                    lsize = os.path.getsize(lockpath)
                    rem, kb2 = _remove_file(lockpath, lsize)
                    if rem:
                        freed_kb += kb2
                
                # Also remove companion .trajectory.jsonl file
                traj = f.replace(".jsonl", ".trajectory.jsonl")
                if os.path.exists(traj):
                    tsize = os.path.getsize(traj)
                    rem, kb2 = _remove_file(traj, tsize)
                    if rem:
                        freed_kb += kb2
                
                # Also remove companion .checkpoint.*.jsonl files
                base = f.rsplit(".jsonl", 1)[0]
                checkpoint_glob = f"{base}.checkpoint.*.jsonl"
                for cp in glob.glob(checkpoint_glob):
                    if os.path.exists(cp):
                        csize = os.path.getsize(cp)
                        rem, kb2 = _remove_file(cp, csize)
                        if rem:
                            freed_kb += kb2
        except (IOError, OSError) as e:
            _total_warnings += 1
            print(f"  [WARN] Error processing {fn}: {e}")
            continue
    
    return deleted, freed_kb


def cleanup_old_trajectories():
    """Delete .trajectory.jsonl and .checkpoint.*.jsonl files older than their max age.
    Also force-clean trajectory files >10MB regardless of age (prevents lock timeouts).
    Returns (files_removed, freed_kb)."""
    global _total_warnings
    now = time.time()
    traj_max_age = TRAJECTORY_MAX_AGE_DAYS * 86400
    checkpoint_max_age = CHECKPOINT_MAX_AGE_DAYS * 86400
    sessions_dir = os.path.dirname(SESSION_GLOB)
    removed = 0
    freed_kb = 0.0

    # Clean old .trajectory.jsonl files
    for f in glob.glob(os.path.join(sessions_dir, "*.trajectory.jsonl")):
        try:
            mtime = os.path.getmtime(f)
            age = now - mtime
            fsize = os.path.getsize(f)
            size_kb = fsize / 1024
            # Force-clean: >10MB regardless of age (prevents write lock timeouts)
            # But NEVER delete active trajectory (age < 300s = 5 min)
            force_clean = (size_kb > TRAJECTORY_FORCE_CLEAN_KB and age > 300)
            if age > traj_max_age or force_clean:
                rem, kb = _remove_file(f, fsize)
                if rem:
                    removed += 1
                    freed_kb += kb
                    if force_clean:
                        _total_warnings += 1
                        print(f"  [FORCE-CLEAN] {os.path.basename(f)} — {size_kb:.0f}KB (> {TRAJECTORY_FORCE_CLEAN_KB}KB limit)")
        except (IOError, OSError) as e:
            _total_warnings += 1
            print(f"  [WARN] Error processing {os.path.basename(f)}: {e}")
            continue

    # Clean old .checkpoint.*.jsonl files
    for f in glob.glob(os.path.join(sessions_dir, "*.checkpoint.*.jsonl")):
        try:
            mtime = os.path.getmtime(f)
            age = now - mtime
            if age > checkpoint_max_age:
                fsize = os.path.getsize(f)
                rem, kb = _remove_file(f, fsize)
                if rem:
                    removed += 1
                    freed_kb += kb
        except (IOError, OSError) as e:
            _total_warnings += 1
            print(f"  [WARN] Error processing {os.path.basename(f)}: {e}")
            continue

    return removed, freed_kb


def cleanup_bloated_sessions():
    """Auto-clean bloated topic files: >500KB AND older than 2 days.
    Keeps files modified within the last 24h (never delete recent active files).
    Also cleans companion .trajectory.jsonl, .lock, and .checkpoint.*.jsonl files.
    Returns (files_removed, freed_kb)."""
    global _total_warnings
    now = time.time()
    max_age_sec = SESSION_MAX_AGE_DAYS * 86400
    sessions_dir = os.path.dirname(SESSION_GLOB)
    removed = 0
    freed_kb = 0.0

    topic_files = glob.glob(os.path.join(sessions_dir, "*-topic-*.jsonl"))

    for f in topic_files:
        fn = os.path.basename(f)
        try:
            mtime = os.path.getmtime(f)
            age = now - mtime

            # NEVER delete files modified in last 24h (recent active files)
            if age < 86400:
                continue

            fsize = os.path.getsize(f)
            size_kb = fsize / 1024

            # Check: >500KB AND older than 2 days (was 7 — too long, bloat within 2 days)
            if size_kb > SESSION_SIZE_WARN_KB and age > max_age_sec:
                # Remove the topic file
                rem, kb = _remove_file(f, fsize)
                if rem:
                    removed += 1
                    freed_kb += kb

                # Remove companion .lock file
                lockpath = f + ".lock"
                if os.path.exists(lockpath):
                    lsize = os.path.getsize(lockpath)
                    rem2, kb2 = _remove_file(lockpath, lsize)
                    if rem2:
                        freed_kb += kb2

                # Remove companion .trajectory.jsonl file
                # Pattern: replace .jsonl with .trajectory.jsonl
                traj = f.replace(".jsonl", ".trajectory.jsonl")
                if os.path.exists(traj):
                    tsize = os.path.getsize(traj)
                    rem2, kb2 = _remove_file(traj, tsize)
                    if rem2:
                        freed_kb += kb2

                # Remove companion .checkpoint.*.jsonl files
                base = f.rsplit(".jsonl", 1)[0]
                checkpoint_glob = f"{base}.checkpoint.*.jsonl"
                for cp in glob.glob(checkpoint_glob):
                    if os.path.exists(cp):
                        csize = os.path.getsize(cp)
                        rem2, kb2 = _remove_file(cp, csize)
                        if rem2:
                            freed_kb += kb2
        except (IOError, OSError) as e:
            _total_warnings += 1
            print(f"  [WARN] Error processing {fn}: {e}")
            continue

    return removed, freed_kb


def get_session_disk_usage():
    """Calculate disk usage breakdown for session files.
    Returns dict with counts and sizes for each file category."""
    sessions_dir = os.path.dirname(SESSION_GLOB)
    all_jsonl = glob.glob(os.path.join(sessions_dir, "*.jsonl"))

    # Categorize files
    trajectory_files = [f for f in all_jsonl if ".trajectory." in os.path.basename(f)]
    checkpoint_files = [f for f in all_jsonl if ".checkpoint." in os.path.basename(f)]
    main_jsonl_files = [f for f in all_jsonl
                        if ".trajectory." not in os.path.basename(f)
                        and ".checkpoint." not in os.path.basename(f)]
    lock_files = glob.glob(os.path.join(sessions_dir, "*.jsonl.lock"))

    def _total_size(files):
        total = 0
        for f in files:
            try:
                total += os.path.getsize(f)
            except OSError:
                pass
        return total

    usage = {
        "main_jsonl": {
            "count": len(main_jsonl_files),
            "size_kb": _total_size(main_jsonl_files) / 1024,
        },
        "trajectory_jsonl": {
            "count": len(trajectory_files),
            "size_kb": _total_size(trajectory_files) / 1024,
        },
        "checkpoint_jsonl": {
            "count": len(checkpoint_files),
            "size_kb": _total_size(checkpoint_files) / 1024,
        },
        "lock_files": {
            "count": len(lock_files),
        },
        "total_all_kb": 0,
    }
    usage["total_all_kb"] = (
        usage["main_jsonl"]["size_kb"]
        + usage["trajectory_jsonl"]["size_kb"]
        + usage["checkpoint_jsonl"]["size_kb"]
    )

    return usage


def cleanup_own_sessions(keep=MAX_OWN_SESSIONS):
    """Delete old lock monitor cron sessions, keeping only the last <keep>."""
    sessions = []
    for f in glob.glob(SESSION_GLOB):
        fn = os.path.basename(f)
        if "topic-" in fn or ".trajectory." in fn or ".checkpoint." in fn:
            continue
        try:
            fsize = os.path.getsize(f)
            if fsize < 100:
                continue
            with open(f) as fh:
                content = fh.read(2048)
                if "lock_monitor.py --once" in content:
                    sessions.append((os.path.getmtime(f), f))
        except (IOError, OSError, FileNotFoundError):
            continue
    
    sessions.sort(reverse=True)
    deleted = 0
    for _, f in sessions[keep:]:
        try:
            removed, _ = _remove_file(f)
            if removed:
                deleted += 1
            traj = f.replace(".jsonl", ".trajectory.jsonl")
            if os.path.exists(traj):
                _remove_file(traj)
        except (IOError, OSError):
            continue
    
    return deleted


def print_disk_usage_summary():
    """Print a disk usage summary of session files."""
    usage = get_session_disk_usage()
    print()
    print("========== Session Disk Usage ==========")
    print(f"  Main .jsonl files:        {usage['main_jsonl']['count']:>5d} files, {usage['main_jsonl']['size_kb']:>10.0f} KB")
    print(f"  .trajectory.jsonl files:  {usage['trajectory_jsonl']['count']:>5d} files, {usage['trajectory_jsonl']['size_kb']:>10.0f} KB")
    print(f"  .checkpoint.*.jsonl files:{usage['checkpoint_jsonl']['count']:>5d} files, {usage['checkpoint_jsonl']['size_kb']:>10.0f} KB")
    print(f"  .lock files:              {usage['lock_files']['count']:>5d} files")
    print(f"  ------------------------------------------")
    print(f"  TOTAL:                               {usage['total_all_kb']:>10.0f} KB")
    print("==========================================")
    print()
    return usage


def main():
    global DRY_RUN, _total_locks_cleaned, _total_warnings

    # Parse flags
    DRY_RUN = "--dry-run" in sys.argv

    if DRY_RUN:
        print("[LOCK_MONITOR] DRY-RUN mode — no files will be deleted")
        print()

    if "--status" in sys.argv:
        print("## Lock Monitor Status")
        print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        print()

        cleaned, active, report = check_session_locks()
        print(f"### Session Locks: {active} active, {cleaned} cleaned")
        if report:
            for r in report:
                print(r)
        else:
            print("  (none)")

        print()
        issues = check_code_locks()
        print("### Code Locks:")
        if issues:
            for i in issues:
                print(i)
        else:
            print("  ✅ No stale code locks")

        # Also show disk usage in status mode
        print_disk_usage_summary()
        return

    # ── --once mode (for cron) ──

    if DRY_RUN:
        header = "[LOCK_MONITOR] DRY-RUN — would perform the following:"
    else:
        header = f"[LOCK_MONITOR] Run at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    print(header)
    print()

    # 1. Session locks
    cleaned, active, report = check_session_locks()
    if cleaned > 0:
        action = "Would clean" if DRY_RUN else "Cleaned"
        print(f"[LOCK_MONITOR] {action} {cleaned} stale session lock(s)")
        for r in report:
            if "CLEANED" in r:
                print(r)
    elif active > 0:
        print(f"[LOCK_MONITOR] OK: {active} active lock(s), 0 cleaned")
    else:
        print("[LOCK_MONITOR] OK: no locks found")

    # 2. Code locks
    issues = check_code_locks()
    if issues:
        print("[LOCK_MONITOR] WARNING: Code lock issues found")
        _total_warnings += len(issues)
        for i in issues:
            print(i)

    # 3. Session bloat check
    bloat = check_session_bloat()
    if bloat:
        bloat_count = len(bloat)
        _total_warnings += bloat_count
        print(f"[LOCK_MONITOR] WARNING: {bloat_count} session file(s) too large:")
        for name, size in bloat:
            print(f"  {name}: {size:.0f}KB (> {SESSION_SIZE_WARN_KB}KB threshold)")

    # 4. Trajectory bloat check
    traj_warnings = check_trajectory_bloat()
    if traj_warnings:
        _total_warnings += len(traj_warnings)
        print(f"[LOCK_MONITOR] WARNING: {len(traj_warnings)} trajectory file(s) oversized:")
        for name, size in traj_warnings:
            print(f"  {name}: {size:.0f}KB (> {TRAJECTORY_MAX_SIZE_KB}KB threshold)")

    # 5. Old session/topic cleanup
    old_deleted, old_freed = cleanup_old_sessions()
    if old_deleted > 0:
        action = "Would remove" if DRY_RUN else "removed"
        print(f"[LOCK_MONITOR] Old session cleanup: {action} {old_deleted} file(s), freed {old_freed:.0f}KB")

    # 6. Trajectory & checkpoint auto-cleanup
    traj_deleted, traj_freed = cleanup_old_trajectories()
    if traj_deleted > 0:
        action = "Would remove" if DRY_RUN else "removed"
        print(f"[LOCK_MONITOR] Trajectory cleanup: {action} {traj_deleted} file(s), freed {traj_freed:.0f}KB")

    # 7. Bloated session auto-clean
    bloat_deleted, bloat_freed = cleanup_bloated_sessions()
    if bloat_deleted > 0:
        action = "Would remove" if DRY_RUN else "removed"
        print(f"[LOCK_MONITOR] Bloat cleanup: {action} {bloat_deleted} bloated session(s), freed {bloat_freed:.0f}KB")

    # 8. Self-cleanup: keep only last N lock monitor sessions
    self_cleaned = cleanup_own_sessions(keep=MAX_OWN_SESSIONS)
    if self_cleaned > 0:
        action = "Would remove" if DRY_RUN else "removed"
        print(f"[LOCK_MONITOR] Self-cleanup: {action} {self_cleaned} old session(s)")

    # 9. Disk usage summary
    print_disk_usage_summary()

    # 10. Final per-run statistics summary
    print()
    print("=" * 50)
    mode_str = "[DRY-RUN] " if DRY_RUN else ""
    summary = (
        f"[LOCK_MONITOR] {mode_str}SUMMARY: "
        f"{_total_locks_cleaned} locks cleaned, "
        f"{_total_files_removed} files removed, "
        f"{_total_freed_kb:.0f} KB freed, "
        f"{_total_warnings} warnings"
    )
    print(summary)
    print("=" * 50)

    # 11. Final result line (parsed by cron monitors)
    if _total_warnings > 0:
        print(f"=== RESULT: OK (warnings: {_total_warnings}) ===")
    else:
        print("=== RESULT: OK ===")


if __name__ == "__main__":
    main()
