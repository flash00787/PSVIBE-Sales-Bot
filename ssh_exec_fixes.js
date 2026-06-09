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
  const FIX_REGEX_B64 = 'aW1wb3J0IHJlCndpdGggb3BlbignL3Jvb3QvcHN2aWJlX2FwaV9zZXJ2ZXIvZGFzaGJvYXJkX3JvdXRlcy5weScsICdyJykgYXMgZjoKICAgIGxpbmVzID0gZi5yZWFkbGluZXMoKQpvbGQgPSBsaW5lc1sxNzYzXSAgIyAwLWluZGV4ZWQKcHJpbnQoZiJPTEQ6IHtvbGQucnN0cmlwKCl9IikKbmV3ID0gb2xkLnJlcGxhY2UoJzpzKihbZC5dKyknLCByJzpccyooW1xkLl0rKScpCnByaW50KGYiTkVXOiB7bmV3LnJzdHJpcCgpfSIpCmxpbmVzWzE3NjNdID0gbmV3CndpdGggb3BlbignL3Jvb3QvcHN2aWJlX2FwaV9zZXJ2ZXIvZGFzaGJvYXJkX3JvdXRlcy5weScsICd3JykgYXMgZjoKICAgIGYud3JpdGVsaW5lcyhsaW5lcykKcHJpbnQoIkRPTkUgLSBSZWdleCBmaXhlZCIpCg==';
  const FIX_VUE_B64 = 'd2l0aCBvcGVuKCcvcm9vdC9wc3ZpYmUtZGFzaGJvYXJkL3NyYy92aWV3cy9GaW5hbmNlQmFsYW5jZS52dWUnLCAncicpIGFzIGY6CiAgICBjb250ZW50ID0gZi5yZWFkKCkKb2xkID0gJzxkaXYgY2xhc3M9Im1pbi1oLXNjcmVlbiBiZy1ncmF5LTUwIGRhcms6YmctZ3JheS05MDAgcC00IGxnOnAtNiI+JwpuZXcgPSAnPGRpdiBjbGFzcz0icC00IGxnOnAtNiI+JwppZiBvbGQgaW4gY29udGVudDoKICAgIGNvbnRlbnQgPSBjb250ZW50LnJlcGxhY2Uob2xkLCBuZXcpCiAgICB3aXRoIG9wZW4oJy9yb290L3BzdmliZS1kYXNoYm9hcmQvc3JjL3ZpZXdzL0ZpbmFuY2VCYWxhbmNlLnZ1ZScsICd3JykgYXMgZjoKICAgICAgICBmLndyaXRlKGNvbnRlbnQpCiAgICBwcmludCgiRE9ORSAtIFZ1ZSBmaXhlZCIpCmVsc2U6CiAgICBwcmludCgiT0xEIERJViBOT1QgRk9VTkQiKQogICAgZm9yIGksIGxpbmUgaW4gZW51bWVyYXRlKGNvbnRlbnQuc3BsaXQoJ1xuJyksIDEpOgogICAgICAgIGlmICdtaW4taC1zY3JlZW4nIGluIGxpbmU6CiAgICAgICAgICAgIHByaW50KGYnTGluZSB7aX06IHtsaW5lLnN0cmlwKClbOjEyMF19JykK';

  const cmds = [
    {
      label: 'FIX 1: Regex',
      cmd: `echo '${FIX_REGEX_B64}' | base64 -d | python3`,
    },
    {
      label: 'FIX 2: Vue',
      cmd: `echo '${FIX_VUE_B64}' | base64 -d | python3`,
    },
    {
      label: 'VERIFY regex line',
      cmd: `sed -n '1764p' /root/psvibe_api_server/dashboard_routes.py`,
    },
    {
      label: 'VERIFY vue line 2',
      cmd: `sed -n '2p' /root/psvibe-dashboard/src/views/FinanceBalance.vue`,
    },
  ];

  for (const { label, cmd } of cmds) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, 30000);
      console.log(`Exit: ${r.code}`);
      console.log(r.stdout);
      if (r.stderr) console.log('STDERR:', r.stderr);
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
}

runFixes().catch(e => console.error('FATAL:', e));
