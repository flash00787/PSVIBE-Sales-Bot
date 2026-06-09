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
  // Find route definitions in the API server
  console.log("===== Route patterns =====");
  try {
    const r = await sshExec('grep -n "@app\.\|@router\.\|create_booking\|end_booking\|cancel_booking\|save_attendance\|add_console_game\|remove_console_game\|set_game_disc_count\|update_game_library_install\|add_console_to_setting\|remove_console_from_setting" /root/psvibe_api_server/app.py | head -60');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
}
main();
