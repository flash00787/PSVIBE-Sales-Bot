const { Client } = require('ssh2');
const fs = require('fs');

function sshExec(command, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let result = '';
    let err = '';
    const timer = setTimeout(() => { conn.end(); reject(new Error('Timeout')); }, timeout);
    conn.on('ready', () => {
      conn.exec(command, (e, stream) => {
        if (e) { clearTimeout(timer); conn.end(); return reject(e); }
        stream.on('data', d => result += d.toString());
        stream.stderr.on('data', d => err += d.toString());
        stream.on('close', () => {
          clearTimeout(timer);
          conn.end();
          resolve({ stdout: result, stderr: err });
        });
      });
    });
    conn.on('error', e => { clearTimeout(timer); reject(e); });
    conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
  });
}

async function main() {
  // Check if api_client.py exists on VPS
  console.log("===== Check api_client.py =====");
  try {
    const r = await sshExec('ls -la /root/psvibe-sale-bot/bot/api_client.py 2>&1; echo "---"; head -50 /root/psvibe-sale-bot/bot/api_client.py 2>&1');
    console.log(r.stdout);
    if (r.stderr) console.log('STDERR:', r.stderr);
  } catch(e) { console.error(e); }

  console.log("\n===== Check _HAS_API in __init__.py =====");
  try {
    const r = await sshExec('grep -n "_HAS_API\|from bot.api_client\|api_create_booking\|api_end_booking\|api_cancel_booking\|api_save_attendance\|api_add_console_game\|api_remove_console_game\|api_set_game_disc_count\|api_update_game_library_install\|api_add_console_to_setting\|api_remove_console_from_setting" /root/psvibe-sale-bot/bot/__init__.py 2>&1');
    console.log(r.stdout);
    if (r.stderr) console.log('STDERR:', r.stderr);
  } catch(e) { console.error(e); }

  console.log("\n===== Check bot directory listing =====");
  try {
    const r = await sshExec('ls -la /root/psvibe-sale-bot/bot/');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
}

main();
