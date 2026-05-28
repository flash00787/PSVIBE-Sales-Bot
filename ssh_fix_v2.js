const { Client } = require('ssh2');
const fs = require('fs');

// Python script to apply the fixes properly
const pythonFix = `
import re

with open('/root/Personal-Wallet-Tele-Bot-2/bot/main.py', 'r') as f:
    code = f.read()
original = code

# ---- FIX 1: Import TelegramConflict ----
# Add Conflict import after "from telegram import ("
code = code.replace(
    'from telegram import (',
    'from telegram import (\\n    Conflict as TelegramConflict,'
)

# ---- FIX 2: Replace error_handler ----
old_error_handler = '''async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Use /cancel to reset and try again."
            )
        except Exception:
            pass'''

new_error_handler = '''async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    if isinstance(err, TelegramConflict):
        logger.critical(
            "Telegram API Conflict (409) — another instance may be polling. "
            "Stopping bot to restart with fresh connection."
        )
        try:
            app = context.application
            if app.running:
                await app.stop()
        except Exception as stop_err:
            logger.error(f"Failed to stop app during Conflict: {stop_err}")
        return
    logger.error("Unhandled exception", exc_info=err)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Use /cancel to reset and try again."
            )
        except Exception:
            pass'''

assert old_error_handler in code, "Could not find error_handler to replace!"
code = code.replace(old_error_handler, new_error_handler, 1)

# ---- FIX 3: Modify self-healing loop ----
old_loop = '''    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
        except SystemExit:
            break
        except RuntimeError as e:
            if "event loop is closed" in str(e).lower():
                break
            logger.error("Crash — restarting in 5s", exc_info=True)
            time.sleep(5)
        except Exception:
            logger.error("Crash — restarting in 5s", exc_info=True)
            time.sleep(5)'''

new_loop = '''    while True:
        try:
            main()
            logger.info("main() returned cleanly — restarting in 10s")
            time.sleep(10)
        except KeyboardInterrupt:
            break
        except SystemExit:
            break
        except TelegramConflict as e:
            logger.critical(f"Telegram Conflict — restarting in 60s: {e}")
            time.sleep(60)
        except RuntimeError as e:
            if "event loop is closed" in str(e).lower():
                break
            logger.error("Crash — restarting in 10s", exc_info=True)
            time.sleep(10)
        except Exception:
            logger.error("Crash — restarting in 10s", exc_info=True)
            time.sleep(10)'''

assert old_loop in code, "Could not find self-healing loop to replace!"
code = code.replace(old_loop, new_loop, 1)

with open('/root/Personal-Wallet-Tele-Bot-2/bot/main.py', 'w') as f:
    f.write(code)

# Verify syntax
import py_compile
try:
    py_compile.compile('/root/Personal-Wallet-Tele-Bot-2/bot/main.py', doraise=True)
    print("SYNTAX OK")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    # Restore original
    with open('/root/Personal-Wallet-Tele-Bot-2/bot/main.py', 'w') as f:
        f.write(original)
    print("RESTORED ORIGINAL")
`;

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected - applying Python fixes');
  
  conn.exec(`python3 << 'PYEOF'\n${pythonFix}\nPYEOF`, { pty: false }, (err, stream) => {
    if (err) {
      console.log('EXEC ERROR:', err);
      conn.end();
      return;
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += data.toString(); });
    stream.on('close', (code) => {
      console.log(output);
      console.log(`Exit code: ${code}`);
      conn.end();
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
