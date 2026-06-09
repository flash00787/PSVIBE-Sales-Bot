const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

const commands = [
  { label: 'CUSTOMER_BOT_SERVICE', cmd: `echo "=== CUSTOMER BOT SERVICE ===" && cat /etc/systemd/system/psvibe_customer_bot.service ; echo "---" && systemctl status psvibe_customer_bot.service 2>/dev/null | head -20 ; echo "---DONE---"` },
  { label: 'N8N_DETAILS', cmd: `echo "=== N8N DOCKER ===" && docker ps -a --filter name=n8n --format '{{.ID}} {{.Names}} {{.Status}} {{.Image}}' 2>/dev/null ; echo "---" && find / -maxdepth 4 -name "n8n" -type d 2>/dev/null ; echo "---" && docker ps --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null ; echo "---DONE---"` },
  { label: 'DOCKER_COMPOSE_CONTENTS', cmd: `echo "=== OPENCLAW DOCKER-COMPOSE ===" && cat /opt/openclaw/docker-compose.yml 2>/dev/null ; echo "=== CONSTRUCTION DOCKER-COMPOSE ===" && cat /opt/construction-bot/docker-compose.yml 2>/dev/null ; echo "---DONE---"` },
  { label: 'SCRIPT_FULL', cmd: `echo "=== clean-coco-processing.sh ===" && cat /root/scripts/clean-coco-processing.sh ; echo "=== check-coco-telegram.sh ===" && cat /root/scripts/check-coco-telegram.sh ; echo "=== construction-bot-manager.sh ===" && cat /root/scripts/construction-bot-manager.sh ; echo "---DONE---"` },
  { label: 'ROLLBACK_V1', cmd: `echo "=== rollback_v1.sh ===" && cat /root/staging/scripts/rollback_v1.sh ; echo "---DONE---"` },
];

let currentIdx = 0;
let allOutput = '';

function runNext() {
  if (currentIdx >= commands.length) {
    fs.writeFileSync('/home/node/.openclaw/workspace/agent2-output2.txt', allOutput);
    console.log('ALL DONE. Output written to agent2-output2.txt');
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
