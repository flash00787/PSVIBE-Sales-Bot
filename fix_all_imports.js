#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Fix ALL handler files: from bot import now_mmt -> from bot import *
  c.exec(`
echo '=== FIXING ALL HANDLER FILES ==='
echo ''
for f in /root/Sales-Tele-Bot_refactored/bot/handlers/*.py; do
  fname=$(basename "$f")
  if grep -q 'from bot import now_mmt' "$f"; then
    sed -i 's/from bot import now_mmt/from bot import */' "$f"
    echo "  FIXED: $fname"
  fi
done
echo ''
echo '=== VERIFY FIX ==='
for f in /root/Sales-Tele-Bot_refactored/bot/handlers/*.py; do
  first=$(head -1 "$f")
  echo "$(basename $f): $first"
done
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
