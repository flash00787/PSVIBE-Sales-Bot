const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const SERVICE_FILES = [
  {
    path: '/etc/systemd/system/psvibe-api-server.service',
    label: 'psvibe-api-server',
    content: `[Unit]
Description=PS VIBE API Server
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/psvibe_api_server
ExecStart=/root/psvibe_api_server/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
EnvironmentFile=/etc/psvibe/secrets.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target`
  },
  {
    path: '/etc/systemd/system/psvibe-sale-bot.service',
    label: 'psvibe-sale-bot',
    content: `[Unit]
Description=PS VIBE Sales Bot
After=network.target psvibe-api-server.service
Requires=psvibe-api-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/psvibe-sale-bot
ExecStart=/root/venv/bin/python3 main.py
EnvironmentFile=/etc/psvibe/secrets.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target`
  },
  {
    path: '/etc/systemd/system/psvibe-customer.service',
    label: 'psvibe-customer',
    content: `[Unit]
Description=PS VIBE Customer Bot
After=network.target psvibe-api-server.service
Requires=psvibe-api-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/psvibe-sale-bot/customer_bot
ExecStart=/root/venv/bin/python3 main.py
EnvironmentFile=/etc/psvibe/secrets.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target`
  }
];

const results = [];

function execCommand(cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '';
      let stderr = '';
      stream.on('data', (data) => stdout += data.toString());
      stream.stderr.on('data', (data) => stderr += data.toString());
      stream.on('close', (code) => {
        resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
      });
    });
  });
}

async function main() {
  const privateKey = fs.readFileSync(
    path.join(process.env.HOME, '.openclaw/workspace/.ssh/id_rsa')
  );

  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({
      host: '5.223.81.16',
      port: 22,
      username: 'root',
      privateKey: privateKey
    });
  });

  console.log('=== Connected to VPS ===\n');

  // Process each service
  for (const svc of SERVICE_FILES) {
    console.log(`--- ${svc.label} ---`);

    // Step 1: Check if file exists
    let exists = false;
    try {
      const check = await execCommand(`test -f "${svc.path}" && echo "EXISTS" || echo "NOT_EXISTS"`);
      exists = check.stdout.includes('EXISTS');
      console.log(`  Check exists: ${exists ? 'YES' : 'NO'}`);
    } catch (e) {
      console.log(`  Check exists: ERROR (${e.message}), assuming not exists`);
    }

    // Step 2: Write the file
    const escapedContent = svc.content
      .replace(/\\/g, '\\\\')
      .replace(/'/g, "'\\''")
      .replace(/\$/g, '\\$');

    const writeCmd = `cat > '${svc.path}' << 'SVC_EOF'\n${svc.content}\nSVC_EOF`;
    const writeResult = await execCommand(writeCmd);
    console.log(`  Write file: ${writeResult.code === 0 ? 'OK' : 'FAIL'}`);
    if (writeResult.stderr) console.log(`  stderr: ${writeResult.stderr}`);

    results.push({
      service: svc.label,
      path: svc.path,
      existedBefore: exists,
      writeSuccess: writeResult.code === 0,
      writeError: writeResult.stderr || null
    });
  }

  // Step 3: daemon-reload
  console.log('\n--- daemon-reload ---');
  const reload = await execCommand('systemctl daemon-reload');
  console.log(`  Result: ${reload.code === 0 ? 'OK' : 'FAIL'}`);
  if (reload.stderr) console.log(`  stderr: ${reload.stderr}`);

  // Step 4: Enable and start each service
  console.log('\n--- Enable & Start ---');
  for (const svc of SERVICE_FILES) {
    console.log(`\n--- ${svc.label} ---`);

    // Enable
    const enable = await execCommand(`systemctl enable ${svc.label}`);
    console.log(`  Enable: ${enable.code === 0 ? 'OK' : 'FAIL (code ' + enable.code + ')'}`);
    if (enable.stderr) console.log(`  stderr: ${enable.stderr}`);
    if (enable.stdout) console.log(`  stdout: ${enable.stdout}`);

    // Start
    const start = await execCommand(`systemctl start ${svc.label}`);
    console.log(`  Start: ${start.code === 0 ? 'OK' : 'FAIL (code ' + start.code + ')'}`);
    if (start.stderr) console.log(`  stderr: ${start.stderr}`);
    if (start.stdout) console.log(`  stdout: ${start.stdout}`);

    // Status check
    const status = await execCommand(`systemctl is-active ${svc.label} 2>&1`);
    const isActive = status.stdout.trim();
    console.log(`  Status: ${isActive}`);

    // Update results
    const entry = results.find(r => r.service === svc.label);
    entry.enableSuccess = enable.code === 0;
    entry.enableError = enable.stderr || null;
    entry.startSuccess = start.code === 0;
    entry.startError = start.stderr || null;
    entry.activeStatus = isActive;
  }

  // Write results file
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  let report = `# Systemd Service Files - Fix Report\n\n`;
  report += `**Date:** ${now}\n`;
  report += `**VPS:** 5.223.81.16\n\n`;
  report += `## Results\n\n`;

  for (const r of results) {
    report += `### ${r.service}\n`;
    report += `- **File:** \`${r.path}\`\n`;
    report += `- **Existed before:** ${r.existedBefore ? 'Yes' : 'No'}\n`;
    report += `- **Write:** ${r.writeSuccess ? '✅ Success' : '❌ Failed'}\n`;
    if (r.writeError) report += `- **Write Error:** \`${r.writeError}\`\n`;
    report += `- **Enable:** ${r.enableSuccess ? '✅ Success' : '❌ Failed'}\n`;
    if (r.enableError) report += `- **Enable Error:** \`${r.enableError}\`\n`;
    report += `- **Start:** ${r.startSuccess ? '✅ Success' : '❌ Failed'}\n`;
    if (r.startError) report += `- **Start Error:** \`${r.startError}\`\n`;
    report += `- **Active Status:** ${r.activeStatus}\n\n`;
  }

  report += `## Service Contents\n\n`;

  for (const svc of SERVICE_FILES) {
    report += `### ${svc.label}\n\`\`\`ini\n${svc.content}\n\`\`\`\n\n`;
  }

  const reportPath = path.join(process.env.HOME, '.openclaw/workspace/audit/fix_systemd.md');
  const auditDir = path.dirname(reportPath);
  if (!fs.existsSync(auditDir)) fs.mkdirSync(auditDir, { recursive: true });
  fs.writeFileSync(reportPath, report);

  console.log(`\n=== Report written to ${reportPath} ===`);
  conn.end();
}

main().catch(err => {
  console.error('FATAL:', err.message);
  process.exit(1);
});
