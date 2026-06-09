const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const commands = [
  { label: 'SYSTEMD_SERVICES', cmd: `echo "=== SYSTEMD PSVIBE/BOT SERVICES ===" && systemctl list-units --type=service --all | grep -iE "psvibe|bot|wallet|construction|coco" ; echo "---" && ls -la /etc/systemd/system/*psvibe* /etc/systemd/system/*bot* /etc/systemd/system/*wallet* /etc/systemd/system/*construction* 2>/dev/null ; echo "---DONE---"` },
  { label: 'SERVICE_FILES_CONTENTS', cmd: `for f in /etc/systemd/system/psvibe-* /etc/systemd/system/*wallet* /etc/systemd/system/*construction* /etc/systemd/system/acm-* /etc/systemd/system/yyo-*; do [ -f "$f" ] && echo "=== $f ===" && cat "$f" && echo ""; done 2>/dev/null ; echo "---DONE---"` },
  { label: 'STAGING_SCRIPTS', cmd: `echo "=== STAGING SCRIPTS ===" && ls -laR /root/staging/scripts/ 2>/dev/null ; echo "---DONE---"` },
  { label: 'ROOT_SCRIPTS', cmd: `echo "=== ROOT SCRIPTS ===" && ls -la /root/scripts/ 2>/dev/null ; echo "=== ROOT SCRIPT HEADS ===" && for f in /root/scripts/*.sh; do [ -f "$f" ] && echo "=== $f ===" && head -5 "$f" && echo "..."; done 2>/dev/null ; echo "---DONE---"` },
  { label: 'CRONTAB', cmd: `echo "=== CRONTAB ===" && crontab -l 2>/dev/null || echo "(no crontab)" ; echo "---" && ls -la /etc/cron.d/* 2>/dev/null | grep -v "sysstat\|anacron" ; echo "---DONE---"` },
  { label: 'N8N', cmd: `echo "=== N8N DIR ===" && ls -la /root/.n8n/ 2>/dev/null | head -20 ; echo "---" && ls -la /root/.n8n/database* 2>/dev/null ; echo "---DONE---"` },
  { label: 'DOCKER_COMPOSE', cmd: `echo "=== DOCKER-COMPOSE ===" && find /root /opt /etc -maxdepth 5 -name "docker-compose*" -o -name "compose*.yml" -o -name "compose*.yaml" 2>/dev/null | head -10 ; echo "---DONE---"` },
  { label: 'DEPLOY_SCRIPTS', cmd: `echo "=== DEPLOY.SH ===" && cat /root/staging/scripts/deploy.sh 2>/dev/null ; echo "=== ROLLBACK.SH ===" && cat /root/staging/scripts/rollback.sh 2>/dev/null ; echo "---DONE---"` },
  { label: 'ALL_SERVICES', cmd: `echo "=== ALL SYSTEMD UNITS ===" && ls -la /etc/systemd/system/*.service 2>/dev/null ; echo "---" && ls -la /etc/systemd/system/multi-user.target.wants/ 2>/dev/null ; echo "---DONE---"` },
  { label: 'N8N_CONFIG', cmd: `echo "=== N8N ENV/CONFIG ===" && cat /root/.n8n/.env 2>/dev/null ; echo "---" && cat /etc/n8n* 2>/dev/null ; echo "---" && find /root/.n8n -name "*.json" -not -path "*/binaryData/*" 2>/dev/null | head -10 ; echo "---DONE---"` },
];

let currentIdx = 0;
let allOutput = '';

function runNext() {
  if (currentIdx >= commands.length) {
    // Write output
    fs.writeFileSync('/home/node/.openclaw/workspace/agent2-output.txt', allOutput);
    console.log('ALL DONE. Output written to agent2-output.txt');
    conn.end();
    return;
  }

  const { label, cmd } = commands[currentIdx];
  console.log(`\n[${currentIdx + 1}/${commands.length}] Running: ${label}`);
  
  conn.exec(cmd, (err, stream) => {
    if (err) {
      allOutput += `\n=== ${label} ===\nERROR: ${err.message}\n\n`;
      currentIdx++;
      runNext();
      return;
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += 'STDERR: ' + data.toString(); });
    stream.on('close', (code) => {
      allOutput += `\n=== ${label} (exit ${code}) ===\n${output}\n\n`;
      currentIdx++;
      runNext();
    });
  });
}

conn.on('ready', () => {
  console.log('Connected to 5.223.81.16');
  runNext();
});

conn.on('error', (err) => {
  console.error('Connection error:', err.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
});
