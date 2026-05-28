import { Client } from 'ssh2';
import fs from 'fs';

const HOST = '167.71.196.120';
const USER = 'root';
const PASS = 'Freedom2024#RevFlash';
const OUTDIR = '/home/node/.openclaw/workspace/audit_output/';

fs.mkdirSync(OUTDIR, { recursive: true });

const commands = [
  // File contents
  { name: 'package.json', cmd: 'cat /opt/agri-bot/package.json' },
  { name: 'env.txt', cmd: 'cat /opt/agri-bot/.env 2>/dev/null || echo "NO .env FILE"' },
  { name: 'secrets.txt', cmd: 'cat /opt/agri-bot/.secrets 2>/dev/null || echo "NO .secrets FILE"' },
  { name: 'ecosystem.txt', cmd: 'cat /opt/agri-bot/ecosystem.config.cjs' },
  { name: 'start.sh', cmd: 'cat /opt/agri-bot/start.sh' },
  { name: 'dist_head.txt', cmd: 'head -300 /opt/agri-bot/dist/index.mjs' },
  { name: 'dist_tail.txt', cmd: 'tail -300 /opt/agri-bot/dist/index.mjs' },
  { name: 'dist_wc.txt', cmd: 'wc -l -c /opt/agri-bot/dist/index.mjs' },
  { name: 'error_log.txt', cmd: 'tail -200 /root/.pm2/logs/agri-bot-error.log 2>/dev/null || echo "NO ERROR LOG"' },
  { name: 'out_log.txt', cmd: 'tail -200 /root/.pm2/logs/agri-bot-out.log 2>/dev/null || echo "NO OUT LOG"' },
  { name: 'ls_agri.txt', cmd: 'ls -laR /opt/agri-bot/' },
  { name: 'src_files.txt', cmd: 'ls -la /opt/agri-bot/src/ 2>/dev/null && echo "---FILE PATHS---" && find /opt/agri-bot/src/ -name "*.ts" -type f 2>/dev/null || echo "NO SRC DIR"' },
  { name: 'pm2_describe.txt', cmd: 'pm2 describe agri-bot 2>/dev/null || echo "PM2 NOT FOUND OR BOT NOT REGISTERED"' },
  { name: 'pm2_list.txt', cmd: 'pm2 list 2>/dev/null || echo "PM2 NOT INSTALLED"' },
  { name: 'npm_audit.txt', cmd: 'cd /opt/agri-bot && npm audit 2>&1 || echo "NPM AUDIT FAILED"' },
  { name: 'npm_ls.txt', cmd: 'cd /opt/agri-bot && npm ls --depth=0 2>&1' },
  { name: 'system.txt', cmd: 'echo "=== UNAME ===" && uname -a && echo "=== NODE ===" && node -v && echo "=== NPM ===" && npm -v && echo "=== PM2 ===" && pm2 -v 2>/dev/null && echo "=== FREE ===" && free -h && echo "=== DF ===" && df -h / && echo "=== UPTIME ===" && uptime && echo "=== NETSTAT ===" && netstat -tlnp 2>/dev/null || ss -tlnp && echo "=== PS AGRI ===" && ps aux | grep -i agri' },
  { name: 'google_sa_exists.txt', cmd: 'test -f /opt/agri-bot/.google-sa.json && echo "EXISTS ($(wc -c < /opt/agri-bot/.google-sa.json) bytes)" || echo "NOT FOUND"' },
  { name: 'ga_key_preview.txt', cmd: 'cat /opt/agri-bot/.google-sa.json 2>/dev/null | head -20 || echo "NO FILE"' },
  { name: 'listening_ports.txt', cmd: 'ss -tlnp | grep -i node' },
  { name: 'caddy_conf.txt', cmd: 'cat /etc/caddy/Caddyfile 2>/dev/null || echo "NO CADDY CONFIG"' },
];

async function runCommand(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let out = '';
      let errOut = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.stderr.on('data', (d) => { errOut += d.toString(); });
      stream.on('close', () => resolve(out + (errOut ? '\n---STDERR---\n' + errOut : '')));
      stream.on('error', reject);
    });
  });
}

async function main() {
  const conn = new Client();
  return new Promise((resolve, reject) => {
    conn.on('ready', async () => {
      console.log('✅ Connected to VPS');
      try {
        for (const item of commands) {
          console.log(`📄 Fetching ${item.name}...`);
          const result = await runCommand(conn, item.cmd);
          fs.writeFileSync(OUTDIR + item.name, result);
          console.log(`   → ${result.length} bytes written`);
        }
        console.log('\n✅ All files collected!');
      } catch (e) {
        console.error('Error:', e);
      }
      conn.end();
      resolve();
    });
    conn.on('error', (e) => {
      console.error('SSH Error:', e);
      reject(e);
    });
    conn.connect({ host: HOST, port: 22, username: USER, password: PASS });
  });
}

main().catch(console.error);
