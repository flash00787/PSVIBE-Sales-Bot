const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();

// The patch script to run on the MAIN VPS (which will ssh into Yangon VPS)
const mainVpsScript = [
  'cat > /tmp/patch_remote.js << "ENDSCRIPT"',
  'const { execSync } = require("child_process");',
  'const pw = "Freedom2024#RevFlash";',
  'const remote = "38.60.254.31";',
  'const ssh = "sshpass -p " + pw + " ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@" + remote;',
  'const patchNodeCode = [',
  '  \'const fs=require("fs");\',',
  '  \'let c=fs.readFileSync("/opt/ibet789-bot/bot.js","utf8");\',',
  '  \'const o=c; const ch=[];\',',
  '  \'c=c.replace(/if \\(\\(await pg\\.\\$/, "if (await isDash(page)"); ch.push("pg_fix");\',',
  '  \'c=c.replace(/{ timeout: 60000, polling: 1000 }/, "{ timeout: 120000, polling: 300 }"); ch.push("timeout");\',',
  '  \'c=c.replace(/return true;.*Default/, "return true;"); ch.push("url");\',',
  '  \'c=c.replace(/typeof _br\\.isConnected === .function. && _br\\.isConnected\\(\\)/g, "_br && (typeof _br.isConnected === "function" ? _br.isConnected() : _br.isConnected)"); ch.push("isConn");\',',
  '  \'c=c.replace(/!_br \\|\\| !_br\\.isConnected\\(\\)/g, "!_br || (typeof _br.isConnected === "function" ? !_br.isConnected() : !_br.isConnected)"); ch.push("keepAlive");\',',
  '  \'if(c!==o){fs.writeFileSync("/opt/ibet789-bot/bot.js",c);console.log("PATCHED: "+ch.join(","));}else{console.log("NO_CHANGES");}\'',
  '].join("");',
  'const cmd = ssh + " \\"systemctl stop ibet789-bot; sleep 1; cd /opt/ibet789-bot && cp bot.js bot.js.bak3 && node -e \\\\"" + Buffer.from(patchNodeCode).toString("base64") + " | base64 -d\\" && systemctl start ibet789-bot; sleep 3; systemctl is-active ibet789-bot; echo DONE\\"";',
  'try {',
  '  const r = execSync(cmd, { timeout: 30000, shell: "/bin/bash" });',
  '  console.log(r.toString());',
  '} catch(e) {',
  '  console.error("ERR:", e.stderr ? e.stderr.toString() : e.message);',
  '}',
  'ENDSCRIPT',
  'node /tmp/patch_remote.js'
].join('\n');

c.on('ready', () => {
  c.exec(mainVpsScript, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', () => { console.log(out); c.end(); process.exit(0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
