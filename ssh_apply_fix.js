const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');

async function sshExec(command, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let output = '';
    let errOutput = '';
    let timer = setTimeout(() => {
      conn.end();
      reject(new Error(`Timeout after ${timeout}ms: ${command.substring(0,100)}`));
    }, timeout);

    conn.on('ready', () => {
      conn.exec(command, (err, stream) => {
        if (err) {
          clearTimeout(timer);
          conn.end();
          return reject(err);
        }
        stream.on('close', (code, signal) => {
          clearTimeout(timer);
          conn.end();
          resolve({ code, stdout: output, stderr: errOutput });
        }).on('data', (data) => { output += data.toString(); })
          .stderr.on('data', (data) => { errOutput += data.toString(); });
      });
    });

    conn.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });

    conn.connect({
      host: HOST,
      port: 22,
      username: USER,
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 15000,
    });
  });
}

async function runFixes() {
  const cmds = [
    {
      label: 'FIX 1: Regex - write Perl script',
      cmd: `cat > /tmp/fix_regex.pl << 'ENDOFSCRIPT'
#!/usr/bin/perl -pi
s/\\(\\[\\^:\\]\\+\\):s\\*\\(\\[d\\.\\]\\+\\)/([^:]+):\\\\s*([\\\\d.]+)/ if $. == 1764;
ENDOFSCRIPT
chmod +x /tmp/fix_regex.pl && perl /tmp/fix_regex.pl /root/psvibe_api_server/dashboard_routes.py && echo "DONE"`,
    },
  ];

  for (const { label, cmd } of cmds) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, 15000);
      console.log(`Exit: ${r.code}`);
      console.log(r.stdout);
      if (r.stderr) console.log('STDERR:', r.stderr);
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }

  // Verify fix
  const verify = [
    {
      label: 'VERIFY: regex line',
      cmd: `sed -n '1764p' /root/psvibe_api_server/dashboard_routes.py`,
    },
  ];
  for (const { label, cmd } of verify) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, 15000);
      console.log(`Exit: ${r.code}`);
      console.log(r.stdout);
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
}

runFixes().catch(e => console.error('FATAL:', e));
