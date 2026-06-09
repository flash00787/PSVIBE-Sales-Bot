const { Client } = require('ssh2');
const fs = require('fs');
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

async function main() {
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 10000 });
  });

  const execCmd = (cmd) => new Promise((res, rej) => {
    conn.exec(cmd, (e, s) => {
      if (e) return rej(e);
      let o = '';
      s.on('data', d => o += d);
      s.stderr.on('data', d => o += d);
      s.on('close', () => res(o.trim()));
    });
  });

  // Find all git repos and their remotes under /root
  const gitRepos = (await execCmd("find /root -maxdepth 4 -name .git -type d 2>/dev/null")).split('\n').filter(Boolean);
  
  for (const gitDir of gitRepos) {
    const repoDir = gitDir.replace('/.git', '');
    const remotes = (await execCmd(`git -C "${repoDir}" remote -v 2>/dev/null`));
    const log = (await execCmd(`git -C "${repoDir}" log --oneline -3 2>/dev/null`));
    const status = (await execCmd(`cd "${repoDir}" && git status --short 2>/dev/null`));
    console.log(`=== ${repoDir} ===`);
    console.log(`Remotes:\n${remotes || '(none)'}`);
    console.log(`Status:\n${status || '(clean)'}`);
    console.log(`Recent:\n${log || '(none)'}`);
    console.log('');
  }

  // Check the working directories specifically
  console.log('=== /root/psvibe-sales-bot (git status) ===');
  console.log(await execCmd("git -C /root/psvibe-sales-bot status 2>&1"));
  console.log('');
  console.log('=== /root/psvibe_api_server (git status) ===');
  console.log(await execCmd("git -C /root/psvibe_api_server status 2>&1"));
  console.log('');

  // Check if psvibe-sales-bot has a remote pointing to Sales-Tele-Bot
  console.log('=== psvibe-sales-bot remote ===');
  console.log(await execCmd("git -C /root/psvibe-sales-bot remote -v 2>&1"));
  console.log('=== psvibe_api_server remote ===');
  console.log(await execCmd("git -C /root/psvibe_api_server remote -v 2>&1"));

  conn.end();
}

main().catch(e => { console.error(e); process.exit(1); });
