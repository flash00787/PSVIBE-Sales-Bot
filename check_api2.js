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
  // Check the actual running API server
  console.log("===== Which API server is running? =====");
  try {
    const r = await sshExec('systemctl status psvibe-api 2>&1 | head -10; echo "---"; cat /etc/systemd/system/psvibe-api.service 2>/dev/null | head -20');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
  
  // Find the running API's app.py
  console.log("\n===== API routes =====");
  try {
    const r = await sshExec('grep -n "def create_booking\|def end_booking\|def cancel_booking\|def save_attendance\|def add_console_game\|def remove_console_game\|def set_game_disc_count\|def update_game_library_install\|def add_console_to_setting\|def remove_console_from_setting" /root/psvibe_api_server/app.py 2>/dev/null');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
}
main();
