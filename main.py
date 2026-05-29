#!/usr/bin/env python3
"""PS VIBE Gaming Lounge — Staff Bot Entry Point."""
import os
import sys
import time
import signal
import asyncio
import logging

from bot import main, keep_alive, ensure_sheet_headers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("/root/psvibe-sales-bot/bot_status.log"),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    import subprocess

    _my_pid = os.getpid()
    _LOCK_PATH = "/tmp/ps_vibe_bot.lock"

    # Kill duplicates
    try:
        _result = subprocess.run(
            ["pgrep", "-f", "python3 main.py"],
            capture_output=True, text=True,
        )
        for _pid_str in _result.stdout.strip().split("\n"):
            try:
                _pid = int(_pid_str.strip())
            except ValueError:
                continue
            if _pid == _my_pid:
                continue
            logging.warning("Duplicate bot (PID %d) — killing...", _pid)
            try:
                os.kill(_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        time.sleep(2)
        for _pid_str in _result.stdout.strip().split("\n"):
            try:
                _pid = int(_pid_str.strip())
            except ValueError:
                continue
            if _pid == _my_pid:
                continue
            try:
                os.kill(_pid, signal.SIGKILL)
                logging.warning("Force-killed PID %d", _pid)
            except ProcessLookupError:
                pass
    except Exception as _e:
        logging.warning("Process scan failed: %s", _e)

    # PID lock
    try:
        with open(_LOCK_PATH, "w") as _lf:
            _lf.write(str(_my_pid))
    except Exception as e_:
        logging.exception("Failed to write PID lock: %s", e_)
    logging.info("Bot started — PID %d", _my_pid)
    ensure_sheet_headers()

    # Health server
    if keep_alive:
        keep_alive()

    # Run once — systemd handles restarts
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by operator.")
    except Exception as exc:
        logging.exception("Bot crashed: %s", exc)
    finally:
        try:
            loop.close()
        except Exception:
            pass

    # Cleanup
    try:
        os.remove(_LOCK_PATH)
    except OSError:
        pass
    logging.info("Bot process exiting (PID %d).", _my_pid)
    sys.exit(0)
