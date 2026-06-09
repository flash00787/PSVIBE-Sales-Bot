import { Client } from 'ssh2';
import { readFileSync } from 'fs';

const conn = new Client();

const PRIVATE_KEY = readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function execCommand(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        if (code !== 0) reject(new Error(`Exit ${code}: ${stderr}`));
        else resolve(stdout);
      });
    });
  });
}

conn.on('ready', async () => {
  try {
    const files = [
      '/root/psvibe-dashboard/src/router/index.ts',
      '/root/psvibe-dashboard/src/views/DashboardView.vue',
      '/root/psvibe-dashboard/src/api/dashboard.ts'
    ];
    for (const f of files) {
      console.log('=== ' + f + ' ===');
      console.log(await execCommand(conn, `cat "${f}"`));
    }
    conn.end();
  } catch (e) {
    console.error('Error:', e.message);
    conn.end();
  }
});

conn.on('error', (err) => { console.error('SSH error:', err.message); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: PRIVATE_KEY,
  readyTimeout: 15000
});
