const { Client } = require('ssh2');
const path = require('path');
const fs = require('fs');

const host = '5.223.81.16';
const username = 'root';
const privateKeyPath = '/home/node/.openclaw/workspace/.ssh/id_rsa';

async function execSSH(command) {
    return new Promise((resolve, reject) => {
        const conn = new Client();
        conn.on('ready', () => {
            conn.exec(command, (err, stream) => {
                if (err) { conn.end(); reject(err); return; }
                let stdout = '', stderr = '';
                stream.on('data', (data) => { stdout += data.toString(); });
                stream.stderr.on('data', (data) => { stderr += data.toString(); });
                stream.on('close', (code) => {
                    conn.end();
                    resolve({ code, stdout, stderr });
                });
            });
        });
        conn.on('error', (err) => reject(err));
        conn.connect({
            host, username,
            privateKey: fs.readFileSync(privateKeyPath, 'utf8')
        });
    });
}

const cmd = process.argv[2];
if (!cmd) { console.error('Usage: node vps_exec.js "COMMAND"'); process.exit(1); }

execSSH(cmd).then(r => {
    console.log(r.stdout);
    if (r.stderr) console.error('STDERR:', r.stderr);
    process.exit(r.code || 0);
}).catch(e => {
    console.error('SSH Error:', e.message);
    process.exit(1);
});
