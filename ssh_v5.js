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
    conn.connect({ host: '167.71.196.120', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
  });
}

async function main() {
  // V2 _load_cfg + _load_members caching
  console.log("===== V2 _load_cfg & _load_members ===== ");
  try {
    const r = await sshExec(`grep -n "_load_cfg\\|_load_members\\|_bg_cache\\|_get_cfg\\|_get_member" /root/staging/bot_src/bot/__init__.py | head -30`);
    console.log(r.stdout);
  } catch(e) {}

  // V2 launch_session_sale / schedule_session_reminder
  console.log("\n===== V2 session_scheduling ===== ");
  try {
    const r = await sshExec(`grep -n "schedule_session\\|launch_session\\|session_reminder" /root/staging/bot_src/bot/__init__.py | head -20`);
    console.log(r.stdout);
  } catch(e) {}

  // V1 NM_REFERRAL - does it exist?
  console.log("\n===== V1 NM_REFERRAL ===== ");
  try {
    const r = await sshExec(`grep -n "NM_REFERRAL" /root/staging/monolithic_ref/main.py | head -10`);
    console.log(r.stdout);
  } catch(e) {}

  // Check for V2 new states not in V1: BOOK_LINK, PROMO_SELECT, etc.
  console.log("\n===== V2 new states (BOOK_LINK, PROMO etc) ===== ");
  try {
    const r = await sshExec(`grep -c "BOOK_LINK\\|PROMO_SELECT\\|BUNDLE_FOC\\|REFERRAL_CODE\\|GAME_EDIT\\|ADJUST_TIME\\|WL_MENU\\|NM_REFERRAL" /root/staging/bot_src/bot/__init__.py`);
    console.log("Occurrences:", r.stdout);
  } catch(e) {}

  // V1 NM_REFERRAL, BOOK_LINK, PROMO_SELECT etc
  console.log("\n===== V1 new states check ===== ");
  try {
    const r = await sshExec(`grep -n "NM_REFERRAL\\|BOOK_LINK\\|PROMO_SELECT\\|BUNDLE_FOC\\|REFERRAL_CODE\\|GAME_EDIT\\|ADJUST_TIME\\|WL_MENU\\|NM_STAFF" /root/staging/monolithic_ref/main.py | head -20`);
    console.log(r.stdout);
  } catch(e) {}
}
main().catch(e => console.error(e));
