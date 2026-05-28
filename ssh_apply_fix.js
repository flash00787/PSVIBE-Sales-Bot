const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected - applying fixes');

  // Fix 1: Add Conflict import
  // Fix 2: Modify error_handler to detect Conflict and stop app
  // Fix 3: Modify self-healing loop for Conflict handling
  
  const commands = [
    // Fix 1: Add Conflict import on line 27 (from telegram import section)
    `sed -i '27s/from telegram import (/from telegram import (\\n    Conflict as TelegramConflict,/' /root/Personal-Wallet-Tele-Bot-2/bot/main.py`,

    // Fix 2: Replace error_handler function (lines 2603-2613)
    `sed -i '2603,2613c\\
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):\\\
    err = context.error\\\
    if isinstance(err, TelegramConflict):\\\
        logger.critical(\\\
            "Telegram API Conflict (409) — another instance may be polling. "\\\
            "Stopping bot to restart with fresh connection."\\\
        )\\\
        try:\\\
            app = context.application\\\
            if app.running:\\\
                await app.stop()\\\
        except Exception as stop_err:\\\
            logger.error(f"Failed to stop app during Conflict: {stop_err}")\\\
        return\\\
    logger.error("Unhandled exception", exc_info=err)\\\
    if isinstance(update, Update) and update.effective_message:\\\
        try:\\\
            await update.effective_message.reply_text(\\\
                "⚠️ An error occurred. Use /cancel to reset and try again."\\\
            )\\\
        except Exception:\\\
            pass' /root/Personal-Wallet-Tele-Bot-2/bot/main.py`,

    // Fix 3: Modify the self-healing loop to add Conflict-specific handling + delay after clean restarts
    // Replace lines 2893-2910 (the while True: loop and its except blocks)
    `sed -i '2893,2910c\\
    while True:\\\
        try:\\\
            main()\\\
            logger.info("main() returned cleanly — restarting in 10s")\\\
            time.sleep(10)\\\
        except KeyboardInterrupt:\\\
            break\\\
        except SystemExit:\\\
            break\\\
        except TelegramConflict as e:\\\
            logger.critical(f"Telegram Conflict — restarting in 60s: {e}")\\\
            time.sleep(60)\\\
        except RuntimeError as e:\\\
            if "event loop is closed" in str(e).lower():\\\
                break\\\
            logger.error("Crash — restarting in 10s", exc_info=True)\\\
            time.sleep(10)\\\
        except Exception:\\\
            logger.error("Crash — restarting in 10s", exc_info=True)\\\
            time.sleep(10)' /root/Personal-Wallet-Tele-Bot-2/bot/main.py`,
  ];

  let idx = 0;
  
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n>>> Fix ${idx}: applying...`);
    conn.exec(cmd, { pty: false }, (err, stream) => {
      if (err) {
        console.log('EXEC ERROR:', err);
        runNext();
        return;
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', (code) => {
        if (output.trim()) console.log('Output:', output.trim());
        console.log(`Exit: ${code}`);
        runNext();
      });
    });
  }

  runNext();
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
