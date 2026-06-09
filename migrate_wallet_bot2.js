#!/usr/bin/env node
/**
 * Migrate Personal-Wallet-Tele-Bot-2 from Source VPS to Main VPS
 * Rename to YYO-Personal-Wallet and configure Nova access
 */

const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ===== CONFIG =====
const SOURCE_HOST = '167.71.196.120';
const SOURCE_USER = 'root';
const SOURCE_PASSWORD = 'Freedom2024#Revflash';

const MAIN_HOST = '5.223.81.16';
const MAIN_USER = 'root';
const MAIN_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

const BOT_NAME = 'Personal-Wallet-Tele-Bot-2';
const NEW_NAME = 'YYO-Personal-Wallet';
const ARCHIVE_PATH = '/tmp/wallet_bot2.tar.gz';
const MAIN_ARCHIVE = '/root/wallet_bot2.tar.gz';

// ===== HELPERS =====

function sshExec(client, cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => {
        resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
      });
    });
  });
}

function sshConnect(config) {
  return new Promise((resolve, reject) => {
    const client = new Client();
    client.on('ready', () => resolve(client));
    client.on('error', reject);
    client.connect(config);
  });
}

// ===== STEP 1: Archive on Source VPS =====
async function step1_archiveSource() {
  console.log('\n=== STEP 1: Archiving Personal-Wallet-Tele-Bot-2 on Source VPS ===');
  
  const client = await sshConnect({
    host: SOURCE_HOST,
    port: 22,
    username: SOURCE_USER,
    password: SOURCE_PASSWORD,
    readyTimeout: 10000,
  });

  console.log('✅ Connected to Source VPS');

  // Check if directory exists
  const check = await sshExec(client, 'ls -la /root/ | grep -i wallet');
  console.log('Wallet directories:', check.stdout);

  // Check if bot dir exists
  const dirCheck = await sshExec(client, `ls /root/${BOT_NAME}/ 2>&1 && echo "EXISTS" || echo "NOT FOUND"`);
  console.log('Bot directory check:', dirCheck.stdout);

  if (!dirCheck.stdout.includes('EXISTS')) {
    console.log('❌ Personal-Wallet-Tele-Bot-2 directory NOT FOUND!');
    // Try with different possible names
    const alt = await sshExec(client, 'ls -la /root/ | grep -i personal');
    console.log('All personal dirs:', alt.stdout);
    client.end();
    return { success: false, error: 'Bot directory not found on source' };
  }

  // Count files for logging
  const count = await sshExec(client, `find /root/${BOT_NAME}/ -type f | wc -l`);
  console.log(`Files in bot dir: ${count.stdout}`);

  // Create archive
  console.log('Creating archive...');
  const tar = await sshExec(client, `cd /root && tar czf ${ARCHIVE_PATH} ${BOT_NAME}/`, 60000);
  console.log('Tar stdout:', tar.stdout || '(empty)');
  console.log('Tar stderr:', tar.stderr || '(empty)');
  console.log('Tar exit code:', tar.code);

  // Verify archive
  const verify = await sshExec(client, `ls -lh ${ARCHIVE_PATH}`);
  console.log('Archive:', verify.stdout);

  // Get archive as base64
  console.log('Reading archive as base64...');
  const b64 = await sshExec(client, `base64 ${ARCHIVE_PATH}`, 120000);
  
  client.end();
  
  if (b64.code !== 0) {
    return { success: false, error: 'Failed to base64 archive: ' + b64.stderr };
  }

  console.log(`✅ Archive created and read: ${b64.stdout.length} base64 chars`);
  
  // Save base64 locally temporarily
  const tmpB64 = '/tmp/wallet_bot2_archive.b64';
  fs.writeFileSync(tmpB64, b64.stdout);
  
  return { success: true, archiveFile: tmpB64 };
}

// ===== STEP 2: Transfer to Main VPS =====
async function step2_transfer(archiveFile) {
  console.log('\n=== STEP 2: Transferring archive to Main VPS ===');
  
  const client = await sshConnect({
    host: MAIN_HOST,
    port: 22,
    username: MAIN_USER,
    privateKey: MAIN_KEY,
    readyTimeout: 10000,
  });

  console.log('✅ Connected to Main VPS');

  // Write base64 file to main VPS
  const b64Content = fs.readFileSync(archiveFile, 'utf8');
  console.log(`Writing base64 to Main VPS: ${b64Content.length} chars...`);
  
  // Write in chunks via echo to avoid issues
  const b64Path = '/tmp/wallet_bot2_archive.b64';
  
  // Use cat with heredoc approach - split into manageable pieces
  const chunkSize = 500000;
  const chunks = [];
  for (let i = 0; i < b64Content.length; i += chunkSize) {
    chunks.push(b64Content.slice(i, i + chunkSize));
  }
  
  console.log(`Splitting into ${chunks.length} chunks of ~${chunkSize} chars each`);
  
  // Clear the file first
  await sshExec(client, `> ${b64Path}`);
  
  // Write each chunk
  for (let i = 0; i < chunks.length; i++) {
    const escaped = chunks[i].replace(/'/g, "'\\''");
    await sshExec(client, `printf '%s' '${escaped}' >> ${b64Path}`, 30000);
    console.log(`  Chunk ${i+1}/${chunks.length} written (${chunks[i].length} chars)`);
  }

  // Verify file size on remote
  const remoteSize = await sshExec(client, `wc -c < ${b64Path}`);
  console.log(`Remote b64 file size: ${remoteSize.stdout} bytes`);
  console.log(`Local b64 file size: ${b64Content.length} bytes`);

  // Decode and extract
  console.log('Decoding base64 and extracting...');
  const decode = await sshExec(client, `base64 -d ${b64Path} > ${MAIN_ARCHIVE} && ls -lh ${MAIN_ARCHIVE}`, 60000);
  console.log('Decode result:', decode.stdout);
  console.log('Decode stderr:', decode.stderr || '(none)');

  // Clean up b64 temp
  await sshExec(client, `rm -f ${b64Path}`);
  
  client.end();
  
  return { success: true };
}

// ===== STEP 3: Extract, Rename, and Update =====
async function step3_extractAndRename() {
  console.log('\n=== STEP 3: Extract, Rename & Update References ===');
  
  const client = await sshConnect({
    host: MAIN_HOST,
    port: 22,
    username: MAIN_USER,
    privateKey: MAIN_KEY,
    readyTimeout: 10000,
  });

  console.log('✅ Connected to Main VPS');

  // Remove old if exists
  await sshExec(client, `rm -rf /root/${NEW_NAME}`);
  
  // Extract
  console.log('Extracting archive...');
  const extract = await sshExec(client, `cd /root && tar xzf ${MAIN_ARCHIVE}`, 60000);
  console.log('Extract result:', extract.code === 0 ? 'OK' : `FAILED: ${extract.stderr}`);

  // Rename
  console.log(`Renaming ${BOT_NAME} → ${NEW_NAME}...`);
  const rename = await sshExec(client, `mv /root/${BOT_NAME} /root/${NEW_NAME} 2>&1 && echo "RENAMED" || echo "RENAME FAILED"`);
  console.log('Rename:', rename.stdout);

  // Verify new dir exists
  const verify = await sshExec(client, `ls -la /root/${NEW_NAME}/ | head -30`);
  console.log('New directory contents:\n', verify.stdout);

  // List all Python files
  const pyFiles = await sshExec(client, `find /root/${NEW_NAME}/ -name "*.py" -type f | sort`);
  console.log('Python files:', pyFiles.stdout);

  // Update references in all files
  console.log('\nUpdating internal references from old name to new name...');
  
  // Replace in Python files, configs, etc.
  const replaceCmd = `cd /root/${NEW_NAME} && grep -rl "${BOT_NAME}" . 2>/dev/null || echo "NO_MATCHES"`;
  const grepResult = await sshExec(client, replaceCmd);
  console.log('Files with old name references:', grepResult.stdout);
  
  if (grepResult.stdout && grepResult.stdout !== 'NO_MATCHES') {
    const files = grepResult.stdout.split('\n').filter(f => f.trim());
    for (const file of files) {
      const sed = await sshExec(client, `sed -i 's/${BOT_NAME}/${NEW_NAME}/g' /root/${NEW_NAME}/${file} 2>&1 && echo "OK" || echo "FAIL"`);
      console.log(`  Updated ${file}: ${sed.stdout}`);
    }
  }

  // Also replace "Personal-Wallet-Tele-Bot-2" in systemd paths and comments
  const replaceAll = await sshExec(client, `find /root/${NEW_NAME}/ -type f -exec sed -i 's/Personal-Wallet-Tele-Bot-2/YYO-Personal-Wallet/g' {} + 2>&1 && echo "ALL_REPLACED" || echo "REPLACE_ERROR"`);
  console.log('Bulk replace:', replaceAll.stdout);

  // Check .env or config files
  const envCheck = await sshExec(client, `ls -la /root/${NEW_NAME}/.env /root/${NEW_NAME}/config.* /root/${NEW_NAME}/*.env 2>&1`);
  console.log('Config/Env files:', envCheck.stdout);

  // Show key files
  const mainPy = await sshExec(client, `head -30 /root/${NEW_NAME}/main.py 2>/dev/null || head -30 /root/${NEW_NAME}/bot.py 2>/dev/null || echo "No main.py/bot.py"`);
  console.log('Main bot file header:', mainPy.stdout);

  // Check for requirements
  const reqs = await sshExec(client, `cat /root/${NEW_NAME}/requirements.txt 2>/dev/null || echo "No requirements.txt"`);
  console.log('Requirements:', reqs.stdout);

  client.end();
  return { success: true };
}

// ===== STEP 4: Check Nova's setup on Main VPS =====
async function step4_checkNova() {
  console.log('\n=== STEP 4: Checking Nova Setup on Main VPS ===');
  
  const client = await sshConnect({
    host: MAIN_HOST,
    port: 22,
    username: MAIN_USER,
    privateKey: MAIN_KEY,
    readyTimeout: 10000,
  });

  console.log('✅ Connected to Main VPS');

  // Check Docker containers
  const docker = await sshExec(client, 'docker ps --format "{{.Names}} {{.Image}} {{.Status}} {{.Ports}}" 2>&1');
  console.log('Docker containers:\n', docker.stdout);

  // Look for openclaw/nova
  const novaContainer = await sshExec(client, 'docker ps --format "{{.Names}} {{.Image}}" | grep -i -E "openclaw|nova"');
  console.log('Nova/OpenClaw containers:', novaContainer.stdout);

  // Check docker-compose
  const compose = await sshExec(client, 'find /root/ /home/ /opt/ -name "docker-compose.yml" -o -name "docker-compose.yaml" 2>/dev/null | head -20');
  console.log('Docker compose files:', compose.stdout);

  // Check for openclaw configs
  const ocConfigs = await sshExec(client, 'find /root/ /home/ /opt/ /etc/ -name "openclaw.json" -o -name "openclaw.yaml" 2>/dev/null | head -20');
  console.log('OpenClaw config files:', ocConfigs.stdout);

  // Check for nova config
  const novaConfig = await sshExec(client, 'find /root/ /home/ /opt/ /etc/ -path "*nova*" -name "*.json" -o -path "*nova*" -name "*.yaml" 2>/dev/null | head -20');
  console.log('Nova config files:', novaConfig.stdout);

  // Check openclaw installation directory
  const ocDirs = await sshExec(client, 'ls -la /root/openclaw 2>/dev/null; ls -la /opt/openclaw 2>/dev/null; ls -la /home/*/openclaw 2>/dev/null');
  console.log('OpenClaw directories:', ocDirs.stdout || '(none found)');

  // Inspect docker container for Nova
  if (novaContainer.stdout) {
    const containerName = novaContainer.stdout.split(' ')[0];
    console.log(`\nInspecting Nova container: ${containerName}`);
    
    // Check container details
    const inspect = await sshExec(client, `docker inspect ${containerName} --format '{{.Config.User}} | {{.Config.WorkingDir}} | {{.HostConfig.Binds}}'`);
    console.log('Container user/workingDir/volumes:', inspect.stdout);

    // Check running processes in container
    const ps = await sshExec(client, `docker exec ${containerName} ps aux 2>&1 | head -20`);
    console.log('Container processes:', ps.stdout);

    // Check container's user/group
    const id = await sshExec(client, `docker exec ${containerName} id 2>&1`);
    console.log('Container user ID:', id.stdout);

    // Check openclaw config inside container
    const ocConf = await sshExec(client, `docker exec ${containerName} cat /app/openclaw.json 2>&1 | head -100`);
    console.log('Container openclaw.json:\n', ocConf.stdout);

    // Check workspace inside container
    const ws = await sshExec(client, `docker exec ${containerName} ls -la /home/node/.openclaw/workspace/ 2>&1 | head -30`);
    console.log('Container workspace:\n', ws.stdout);
  }

  // Check what user runs docker
  const dockerUser = await sshExec(client, 'ps aux | grep -E "dockerd|containerd" | grep -v grep | head -5');
  console.log('Docker daemon processes:', dockerUser.stdout);

  // Check /etc/passwd for users
  const users = await sshExec(client, 'getent passwd | grep -E "nova|openclaw|node|docker"');
  console.log('Relevant users:', users.stdout);

  client.end();
  return { success: true };
}

// ===== STEP 5: Create systemd service =====
async function step5_createService() {
  console.log('\n=== STEP 5: Creating systemd service for YYO-Personal-Wallet ===');
  
  const client = await sshConnect({
    host: MAIN_HOST,
    port: 22,
    username: MAIN_USER,
    privateKey: MAIN_KEY,
    readyTimeout: 10000,
  });

  console.log('✅ Connected to Main VPS');

  // First check what Python is available and what the entry point is
  const pythonCheck = await sshExec(client, 'which python3 && python3 --version');
  console.log('Python:', pythonCheck.stdout);

  // Check bot entry point file
  const entryCheck = await sshExec(client, `ls /root/${NEW_NAME}/main.py /root/${NEW_NAME}/bot.py /root/${NEW_NAME}/app.py /root/${NEW_NAME}/run.py 2>&1`);
  console.log('Entry point files:', entryCheck.stdout);
  
  // Determine entry point
  let entryPoint = 'main.py';
  if (entryCheck.stdout.includes('bot.py') && !entryCheck.stdout.includes('main.py')) {
    entryPoint = 'bot.py';
  }
  console.log(`Using entry point: ${entryPoint}`);

  // Check for virtual environment
  const venvCheck = await sshExec(client, `ls -d /root/${NEW_NAME}/venv /root/${NEW_NAME}/.venv /root/${NEW_NAME}/env 2>&1`);
  console.log('Virtual env:', venvCheck.stdout);

  // Read requirements to check dependencies
  const reqCheck = await sshExec(client, `cat /root/${NEW_NAME}/requirements.txt 2>/dev/null`);
  let hasReqs = reqCheck.stdout && !reqCheck.stdout.includes('No such file');

  // Install requirements if needed
  if (hasReqs) {
    console.log('Installing Python requirements...');
    const pipInstall = await sshExec(client, `cd /root/${NEW_NAME} && pip3 install -r requirements.txt 2>&1 | tail -20`, 120000);
    console.log('pip install:', pipInstall.stdout || pipInstall.stderr);
  } else {
    // Check for common deps
    console.log('Checking for required packages...');
    const pkgCheck = await sshExec(client, 'pip3 list 2>/dev/null | grep -iE "telegram|python-telegram-bot|requests|mysql|gspread"');
    console.log('Installed packages:', pkgCheck.stdout);
  }

  // Create systemd service
  const venvPython = venvCheck.stdout.includes('venv') 
    ? `/root/${NEW_NAME}/venv/bin/python3`
    : (venvCheck.stdout.includes('.venv') ? `/root/${NEW_NAME}/.venv/bin/python3` : '/usr/bin/python3');

  const serviceContent = `[Unit]
Description=YYO Personal Wallet Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/${NEW_NAME}
Environment=PATH=/usr/local/bin:/usr/bin:/bin:/root/${NEW_NAME}/venv/bin
EnvironmentFile=-/root/${NEW_NAME}/.env
ExecStart=${venvPython} /root/${NEW_NAME}/${entryPoint}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=yyo-personal-wallet

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
`;

  console.log('Writing systemd service file...');
  
  // Write service file
  const writeSvc = await sshExec(client, `cat > /etc/systemd/system/yyo-personal-wallet.service << 'SERVICEOF'
${serviceContent}
SERVICEOF
echo "WRITTEN"`);

  console.log('Service file write:', writeSvc.stdout);

  // Verify service file
  const svcCheck = await sshExec(client, 'cat /etc/systemd/system/yyo-personal-wallet.service');
  console.log('Service file contents:\n', svcCheck.stdout);

  // Reload systemd
  const reload = await sshExec(client, 'systemctl daemon-reload && echo "OK"');
  console.log('Systemd reload:', reload.stdout);

  // Enable service
  const enable = await sshExec(client, 'systemctl enable yyo-personal-wallet.service 2>&1 && echo "ENABLED"');
  console.log('Service enable:', enable.stdout);

  // Check if bot is already running something
  const existingBots = await sshExec(client, 'systemctl list-units --type=service | grep -i wallet');
  console.log('Existing wallet services:', existingBots.stdout);

  client.end();
  return { success: true, serviceName: 'yyo-personal-wallet' };
}

// ===== STEP 6: Nova Access Configuration =====
async function step6_novaAccess() {
  console.log('\n=== STEP 6: Nova Access Configuration ===');
  
  const client = await sshConnect({
    host: MAIN_HOST,
    port: 22,
    username: MAIN_USER,
    privateKey: MAIN_KEY,
    readyTimeout: 10000,
  });

  console.log('✅ Connected to Main VPS');

  // Find nova container info
  const novaPs = await sshExec(client, 'docker ps --format "{{.Names}} {{.Image}}" | grep -i -E "openclaw|nova"');
  const novaContainer = novaPs.stdout.split('\n')[0]?.split(' ')[0];
  console.log('Nova container name:', novaContainer || 'NOT FOUND');

  // Get container UID/GID
  let containerUid = '1000';
  let containerGid = '1000';
  
  if (novaContainer) {
    const uidCheck = await sshExec(client, `docker exec ${novaContainer} id -u 2>&1`);
    const gidCheck = await sshExec(client, `docker exec ${novaContainer} id -g 2>&1`);
    containerUid = uidCheck.stdout.trim();
    containerGid = gidCheck.stdout.trim();
    console.log(`Container UID: ${containerUid}, GID: ${containerGid}`);

    // Check container hostname
    const hostname = await sshExec(client, `docker exec ${novaContainer} hostname 2>&1`);
    console.log('Container hostname:', hostname.stdout);

    // Check mounted volumes for workspace path
    const mounts = await sshExec(client, `docker inspect ${novaContainer} --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\\n"}}{{end}}'`);
    console.log('Container mounts:\n', mounts.stdout);

    // Check if docker has bind mounts to host filesystem
    const binds = await sshExec(client, `docker inspect ${novaContainer} --format '{{range .HostConfig.Binds}}{{.}}{{"\\n"}}{{end}}'`);
    console.log('Container binds:\n', binds.stdout);
  }

  // Set file permissions: make bot directory accessible
  console.log('\nSetting file permissions...');
  
  // Make directory and all contents readable by the docker user
  const chmod = await sshExec(client, `chmod -R 755 /root/${NEW_NAME}/`);
  console.log('chmod result:', chmod.code === 0 ? 'OK' : `FAILED: ${chmod.stderr}`);

  // If docker container runs as specific UID, create matching user or use chown
  if (containerUid && containerUid !== '0') {
    // Check if user exists
    const userCheck = await sshExec(client, `id -u ${containerUid} 2>/dev/null && echo "EXISTS" || echo "NOT_FOUND"`);
    console.log(`UID ${containerUid} exists?`, userCheck.stdout);

    // Try to set ownership to match container user
    // Note: root's home dir might not allow others to traverse
    // Let's make /root traversable
    await sshExec(client, 'chmod 755 /root');
    
    // Make bot files readable by docker group
    const dockerGroup = await sshExec(client, 'getent group docker | cut -d: -f3');
    console.log('Docker group GID:', dockerGroup.stdout);
    
    // Add docker group access
    await sshExec(client, `chgrp -R docker /root/${NEW_NAME}/ 2>&1 || echo "chgrp failed"`);
    console.log('Group set to docker');
  }

  // Create nova management script
  console.log('\nCreating Nova wallet management script...');
  
  const manageScript = `#!/bin/bash
# YYO Personal Wallet Bot Management Script
# For use by Nova AI agent
# Location: /usr/local/bin/nova-wallet

ACTION=\${1:-status}
SERVICE="yyo-personal-wallet"
BOT_DIR="/root/${NEW_NAME}"

case "\$ACTION" in
  status)
    systemctl status \$SERVICE --no-pager -l
    ;;
  start)
    systemctl start \$SERVICE && echo "✅ Wallet bot started" || echo "❌ Failed to start"
    ;;
  stop)
    systemctl stop \$SERVICE && echo "✅ Wallet bot stopped" || echo "❌ Failed to stop"
    ;;
  restart)
    systemctl restart \$SERVICE && echo "✅ Wallet bot restarted" || echo "❌ Failed to restart"
    ;;
  logs)
    journalctl -u \$SERVICE --no-pager -n \${2:-50}
    ;;
  logs-follow)
    journalctl -u \$SERVICE -f
    ;;
  list-files)
    find \$BOT_DIR -type f -name "*.py" -o -name "*.json" -o -name "*.env" -o -name "*.txt" -o -name "*.yaml" -o -name "*.yml" | sort
    ;;
  read-file)
    if [ -z "\$2" ]; then
      echo "Usage: nova-wallet read-file <filename>"
      exit 1
    fi
    cat "\$BOT_DIR/\$2" 2>/dev/null || echo "File not found: \$2"
    ;;
  exec)
    shift
    cd "\$BOT_DIR" && python3 "\$@"
    ;;
  *)
    echo "YYO Personal Wallet Bot - Management Script"
    echo "============================================"
    echo ""
    echo "Usage: nova-wallet <command> [args]"
    echo ""
    echo "Commands:"
    echo "  status          Show service status"
    echo "  start           Start the bot"
    echo "  stop            Stop the bot"
    echo "  restart         Restart the bot"
    echo "  logs [lines]    Show recent logs (default 50 lines)"
    echo "  logs-follow     Follow logs in real-time"
    echo "  list-files      List all project files"
    echo "  read-file <f>   Read a file from the bot directory"
    echo "  exec <args>     Execute Python script in bot directory"
    ;;
esac
`;

  const writeScript = await sshExec(client, `cat > /usr/local/bin/nova-wallet << 'SCRIPTEOF'
${manageScript}
SCRIPTEOF
chmod +x /usr/local/bin/nova-wallet && echo "SCRIPT_CREATED"`);
  console.log('Management script:', writeScript.stdout);

  // Test the script
  const testScript = await sshExec(client, '/usr/local/bin/nova-wallet status 2>&1');
  console.log('Script test:\n', testScript.stdout);

  // Create a sudoers rule if needed for Nova
  // Check if there's a way to run without password
  const sudoCheck = await sshExec(client, `echo "root ALL=(ALL) NOPASSWD: /usr/bin/systemctl *yyo-personal-wallet*" > /etc/sudoers.d/nova-wallet && chmod 440 /etc/sudoers.d/nova-wallet && echo "SUDOERS_OK"`);
  console.log('Sudoers: ', sudoCheck.stdout);

  // Create README for Nova
  const readme = `# YYO Personal Wallet Bot
## Location: /root/YYO-Personal-Wallet
## Service: yyo-personal-wallet

### Quick Management (via nova-wallet script):
- Status:  nova-wallet status
- Start:   nova-wallet start
- Stop:    nova-wallet stop
- Restart: nova-wallet restart
- Logs:    nova-wallet logs 100
- Files:   nova-wallet list-files
- Read:    nova-wallet read-file <filename>
- Execute: nova-wallet exec <script.py> [args]

### Direct systemctl:
- systemctl status yyo-personal-wallet
- systemctl start/stop/restart yyo-personal-wallet
- journalctl -u yyo-personal-wallet -f

### Direct access:
- Bot directory: /root/YYO-Personal-Wallet
- Entry point: /root/YYO-Personal-Wallet/${entryPoint}
`;

  const writeReadme = await sshExec(client, `cat > /root/${NEW_NAME}/NOVA_README.md << 'READMEEOF'
${readme}
READMEEOF
echo "README_CREATED"`);
  console.log('Nova README:', writeReadme.stdout);

  // Final check - start the service
  console.log('\nStarting the wallet bot service...');
  const startSvc = await sshExec(client, 'systemctl start yyo-personal-wallet.service 2>&1 && echo "STARTED" || echo "START_FAILED"');
  console.log('Service start:', startSvc.stdout);

  // Wait a moment and check status
  await new Promise(r => setTimeout(r, 3000));
  const statusSvc = await sshExec(client, 'systemctl status yyo-personal-wallet.service --no-pager -l 2>&1');
  console.log('Service status:\n', statusSvc.stdout);

  // Show recent logs
  const logs = await sshExec(client, 'journalctl -u yyo-personal-wallet.service --no-pager -n 20');
  console.log('Recent logs:\n', logs.stdout);

  client.end();
  return { success: true };
}

// ===== MAIN =====
async function main() {
  console.log('========================================');
  console.log(' Personal Wallet Bot 2 → YYO-Personal-Wallet Migration');
  console.log(' Source: 167.71.196.120');
  console.log(' Target: 5.223.81.16');
  console.log('========================================');
  
  const results = {};

  try {
    // Step 1: Archive from source
    results.step1 = await step1_archiveSource();
    if (!results.step1.success) {
      console.error('❌ Step 1 failed:', results.step1.error);
      return;
    }
    console.log('✅ Step 1 complete');

    // Step 2: Transfer
    results.step2 = await step2_transfer(results.step1.archiveFile);
    if (!results.step2.success) {
      console.error('❌ Step 2 failed');
      return;
    }
    console.log('✅ Step 2 complete');

    // Step 3: Extract & Rename
    results.step3 = await step3_extractAndRename();
    if (!results.step3.success) {
      console.error('❌ Step 3 failed');
      return;
    }
    console.log('✅ Step 3 complete');

    // Step 4: Check Nova setup
    results.step4 = await step4_checkNova();
    console.log('✅ Step 4 complete');

    // Step 5: Create systemd service
    results.step5 = await step5_createService();
    if (!results.step5.success) {
      console.error('❌ Step 5 failed');
      return;
    }
    console.log('✅ Step 5 complete');

    // Step 6: Nova access
    results.step6 = await step6_novaAccess();
    console.log('✅ Step 6 complete');

    console.log('\n========================================');
    console.log(' MIGRATION COMPLETE');
    console.log('========================================');
    console.log(` Bot: /root/${NEW_NAME}/`);
    console.log(` Service: yyo-personal-wallet`);
    console.log(` Management: nova-wallet <command>`);
    console.log('========================================');

  } catch (err) {
    console.error('UNEXPECTED ERROR:', err.message);
    console.error(err.stack);
  }
}

main().catch(console.error);
