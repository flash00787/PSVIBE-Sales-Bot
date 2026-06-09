#!/usr/bin/env node
/**
 * Personal-Wallet-Tele-Bot Migration Script
 * Source VPS (167.71.196.120) → Main VPS (5.223.81.16)
 * Rename: "Personal-Wallet-Tele-Bot" → "ACM-Personal-Wallet"
 */

const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');
const { Transform, pipeline } = require('stream');
const { promisify } = require('util');

const pipelineAsync = promisify(pipeline);

// ─── Config ───────────────────────────────────────────────────────────────────
const SOURCE = {
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  password: 'Freedom2024#Revflash',
  readyTimeout: 30000,
  tryKeyboard: true,
  algorithms: {
    kex: [
      'diffie-hellman-group14-sha256',
      'diffie-hellman-group14-sha1',
      'diffie-hellman-group-exchange-sha256',
      'diffie-hellman-group-exchange-sha1',
      'ecdh-sha2-nistp256',
      'ecdh-sha2-nistp384',
      'ecdh-sha2-nistp521',
      'curve25519-sha256',
      'curve25519-sha256@libssh.org',
    ],
    cipher: [
      'aes128-ctr',
      'aes192-ctr',
      'aes256-ctr',
      'aes128-gcm@openssh.com',
      'aes256-gcm@openssh.com',
      'aes256-cbc',
      'aes192-cbc',
      'aes128-cbc',
    ],
    serverHostKey: [
      'ssh-rsa',
      'ssh-dss',
      'ecdsa-sha2-nistp256',
      'ecdsa-sha2-nistp384',
      'ecdsa-sha2-nistp521',
      'ssh-ed25519',
    ],
    hmac: [
      'hmac-sha2-256',
      'hmac-sha2-512',
      'hmac-sha1',
    ],
  },
};

const MAIN_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const MAIN = {
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: MAIN_KEY,
  readyTimeout: 30000,
  keepaliveInterval: 10000,
};

const SOURCE_ARCHIVE = '/tmp/personal_wallet_bot.tar.gz';
const MAIN_ARCHIVE = '/root/personal_wallet_bot.tar.gz';
const SOURCE_DIR = '/root/Personal-Wallet-Tele-Bot';
const MAIN_DIR = '/root/ACM-Personal-Wallet';
const SERVICE_NAME = 'acm-personal-wallet';
const SERVICE_PATH = `/etc/systemd/system/${SERVICE_NAME}.service`;

// ─── Helpers ──────────────────────────────────────────────────────────────────
function sshConnect(client, config) {
  return new Promise((resolve, reject) => {
    client.on('ready', () => resolve());
    client.on('error', (err) => reject(err));
    client.on('timeout', () => reject(new Error('Connection timeout')));
    client.on('keyboard-interactive', (name, instructions, instructionsLang, prompts, finish) => {
      // Respond to keyboard-interactive prompts with password
      finish([config.password || '']);
    });
    client.connect(config);
  });
}

function sshExec(client, cmd, opts = {}) {
  return new Promise((resolve, reject) => {
    const timeout = opts.timeout || 120000;
    const timer = setTimeout(() => reject(new Error(`Command timed out after ${timeout}ms: ${cmd.substring(0, 80)}`)), timeout);
    client.exec(cmd, (err, stream) => {
      if (err) { clearTimeout(timer); return reject(err); }
      let stdout = '', stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => {
        clearTimeout(timer);
        resolve({ code, stdout, stderr });
      });
    });
  });
}

function sftpPutFile(client, localPath, remotePath) {
  return new Promise((resolve, reject) => {
    client.sftp((err, sftp) => {
      if (err) return reject(err);
      const readStream = fs.createReadStream(localPath);
      const writeStream = sftp.createWriteStream(remotePath, {
        mode: 0o644,
        flags: 'w',
      });
      let bytes = 0;
      readStream.on('data', (chunk) => {
        bytes += chunk.length;
        if (bytes % (10 * 1024 * 1024) < chunk.length) {
          process.stderr.write(`  [sftp upload] ${(bytes / 1024 / 1024).toFixed(1)} MB ...\n`);
        }
      });
      pipelineAsync(readStream, writeStream)
        .then(() => resolve(bytes))
        .catch(reject);
    });
  });
}

function sftpGetFile(client, remotePath, localPath) {
  return new Promise((resolve, reject) => {
    client.sftp((err, sftp) => {
      if (err) return reject(err);
      const readStream = sftp.createReadStream(remotePath);
      const writeStream = fs.createWriteStream(localPath);
      let bytes = 0;
      readStream.on('data', (chunk) => {
        bytes += chunk.length;
        if (bytes % (10 * 1024 * 1024) < chunk.length) {
          process.stderr.write(`  [sftp download] ${(bytes / 1024 / 1024).toFixed(1)} MB ...\n`);
        }
      });
      pipelineAsync(readStream, writeStream)
        .then(() => resolve(bytes))
        .catch(reject);
    });
  });
}

function sftpStreamFile(sourceClient, sourcePath, destClient, destPath) {
  return new Promise((resolve, reject) => {
    sourceClient.sftp((err, sourceSftp) => {
      if (err) return reject(err);
      destClient.sftp((err2, destSftp) => {
        if (err2) return reject(err2);
        const readStream = sourceSftp.createReadStream(sourcePath);
        const writeStream = destSftp.createWriteStream(destPath, {
          mode: 0o644,
          flags: 'w',
        });
        let bytes = 0;
        let lastLog = 0;
        readStream.on('data', (chunk) => {
          bytes += chunk.length;
          const mb = Math.floor(bytes / (1024 * 1024));
          if (mb > lastLog) {
            lastLog = mb;
            process.stderr.write(`  [transfer] ${mb} MB ...\n`);
          }
        });
        pipelineAsync(readStream, writeStream)
          .then(() => resolve(bytes))
          .catch(reject);
      });
    });
  });
}

function log(msg) { console.log(`[${new Date().toISOString()}] ${msg}`); }
function success(msg) { console.log(`\x1b[32m✓ ${msg}\x1b[0m`); }
function fail(msg) { console.log(`\x1b[31m✗ ${msg}\x1b[0m`); }
function warn(msg) { console.log(`\x1b[33m⚠ ${msg}\x1b[0m`); }

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  const results = [];
  let sourceClient = null;
  let mainClient = null;

  try {
    // ═══════════════════════════════════════════════════════════════════════════
    // STEP 1: Connect to Source VPS, inspect & archive
    // ═══════════════════════════════════════════════════════════════════════════
    log('STEP 1: Connecting to Source VPS (167.71.196.120) ...');
    sourceClient = new Client();
    await sshConnect(sourceClient, SOURCE);
    success('Connected to Source VPS');

    // List directory structure
    log('Inspecting /root/Personal-Wallet-Tele-Bot/ ...');
    const lsResult = await sshExec(sourceClient, 'ls -la /root/Personal-Wallet-Tele-Bot/ && echo "---" && du -sh /root/Personal-Wallet-Tele-Bot/ && echo "---" && find /root/Personal-Wallet-Tele-Bot/ -type f | head -50');
    console.log(lsResult.stdout);
    if (lsResult.stderr) console.error('STDERR:', lsResult.stderr);
    results.push({ step: '1-inspect', status: 'success' });

    // Create archive (exclude venv if too large, but include it)
    log('Creating tar.gz archive (this may take a minute) ...');
    const archiveResult = await sshExec(sourceClient, 
      `cd /root && tar czf ${SOURCE_ARCHIVE} Personal-Wallet-Tele-Bot/ 2>&1 && echo "ARCHIVE_OK" && ls -lh ${SOURCE_ARCHIVE}`,
      { timeout: 300000 }
    );
    console.log(archiveResult.stdout);
    if (archiveResult.stderr) console.error('STDERR:', archiveResult.stderr);
    
    if (!archiveResult.stdout.includes('ARCHIVE_OK')) {
      throw new Error('Archive creation failed');
    }
    success(`Archive created on Source VPS`);
    results.push({ step: '1-archive', status: 'success' });

    // ═══════════════════════════════════════════════════════════════════════════
    // STEP 2: Connect to Main VPS & transfer file
    // ═══════════════════════════════════════════════════════════════════════════
    log('STEP 2: Connecting to Main VPS (5.223.81.16) ...');
    mainClient = new Client();
    await sshConnect(mainClient, MAIN);
    success('Connected to Main VPS');

    // Transfer via SFTP streaming (source → main directly through gateway)
    log('Transferring archive from Source → Main VPS (streaming via SFTP) ...');
    const transferBytes = await sftpStreamFile(sourceClient, SOURCE_ARCHIVE, mainClient, MAIN_ARCHIVE);
    success(`Transferred ${(transferBytes / 1024 / 1024).toFixed(1)} MB to Main VPS`);
    results.push({ step: '2-transfer', status: 'success', size: `${(transferBytes / 1024 / 1024).toFixed(1)} MB` });

    // Verify archive on Main
    const verifyResult = await sshExec(mainClient, `ls -lh ${MAIN_ARCHIVE} && file ${MAIN_ARCHIVE}`);
    console.log(verifyResult.stdout);
    results.push({ step: '2-verify', status: 'success' });

    // Clean up archive on Source
    await sshExec(sourceClient, `rm -f ${SOURCE_ARCHIVE}`);
    log('Cleaned up archive on Source VPS');

    // ═══════════════════════════════════════════════════════════════════════════
    // STEP 3: Extract & Rename on Main VPS
    // ═══════════════════════════════════════════════════════════════════════════
    log('STEP 3: Extracting archive on Main VPS ...');
    const extractResult = await sshExec(mainClient,
      `cd /root && tar xzf ${MAIN_ARCHIVE} 2>&1 && echo "EXTRACT_OK"`,
      { timeout: 120000 }
    );
    console.log(extractResult.stdout);
    if (extractResult.stderr) console.error(extractResult.stderr);
    
    if (!extractResult.stdout.includes('EXTRACT_OK')) {
      throw new Error('Extraction failed');
    }
    success('Extraction complete');
    results.push({ step: '3-extract', status: 'success' });

    // Rename folder
    log(`Renaming folder: ${SOURCE_DIR} → ${MAIN_DIR}`);
    const renameResult = await sshExec(mainClient, 
      `mv ${SOURCE_DIR} ${MAIN_DIR} 2>&1 && echo "RENAME_OK" && ls -la ${MAIN_DIR}/`
    );
    console.log(renameResult.stdout);
    if (!renameResult.stdout.includes('RENAME_OK')) {
      throw new Error('Rename failed');
    }
    success('Folder renamed');
    results.push({ step: '3-rename-folder', status: 'success' });

    // Search for old name references
    log('Searching for references to old project name ...');
    const grepResult = await sshExec(mainClient, 
      `grep -r "Personal-Wallet-Tele-Bot" ${MAIN_DIR}/ --include="*.py" --include="*.sh" --include="*.env" --include="*.cfg" --include="*.conf" --include="*.json" --include="*.txt" --include="*.service" --include="*.ini" -l 2>/dev/null || echo "NO_MATCHES"`,
      { timeout: 30000 }
    );
    console.log('Files containing old name:');
    console.log(grepResult.stdout);

    const filesToUpdate = grepResult.stdout
      .split('\n')
      .map(l => l.trim())
      .filter(l => l && l !== 'NO_MATCHES');
    
    if (filesToUpdate.length > 0) {
      log(`Updating ${filesToUpdate.length} files with old references ...`);
      // Bulk sed replacement for directory paths
      const sedResult = await sshExec(mainClient,
        `find ${MAIN_DIR}/ -type f \\( -name "*.py" -o -name "*.sh" -o -name "*.env" -o -name "*.cfg" -o -name "*.conf" -o -name "*.json" -o -name "*.txt" -o -name "*.service" -o -name "*.ini" -o -name "*.md" \\) -exec sed -i 's|Personal-Wallet-Tele-Bot|ACM-Personal-Wallet|g' {} + 2>&1 && echo "SED_OK"`
      );
      console.log(sedResult.stdout);
      
      // Also replace display name if present
      await sshExec(mainClient,
        `find ${MAIN_DIR}/ -type f \\( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.txt" \\) -exec sed -i "s|Personal Wallet|ACM's Personal Wallet|g" {} + 2>&1`
      );
      
      success('Code references updated');
    } else {
      log('No references to old name found in code files');
    }
    results.push({ step: '3-rename-references', status: 'success', filesUpdated: filesToUpdate.length });

    // Clean up archive
    await sshExec(mainClient, `rm -f ${MAIN_ARCHIVE}`);
    log('Cleaned up archive on Main VPS');

    // ═══════════════════════════════════════════════════════════════════════════
    // STEP 4: Setup Python environment & systemd service
    // ═══════════════════════════════════════════════════════════════════════════
    log('STEP 4: Setting up Python environment ...');

    // Check if venv exists
    const venvCheck = await sshExec(mainClient, 
      `ls ${MAIN_DIR}/venv/bin/python 2>/dev/null && echo "VENV_EXISTS" || echo "NO_VENV"`,
      { timeout: 10000 }
    );
    console.log('Venv check:', venvCheck.stdout.trim());

    if (venvCheck.stdout.includes('NO_VENV')) {
      log('Creating Python virtual environment ...');
      // Check Python version
      const pyCheck = await sshExec(mainClient, 'python3 --version 2>&1 || python --version 2>&1');
      console.log('Python version:', pyCheck.stdout.trim());

      const venvCreate = await sshExec(mainClient, 
        `cd ${MAIN_DIR} && python3 -m venv venv 2>&1 && echo "VENV_CREATED"`,
        { timeout: 120000 }
      );
      console.log(venvCreate.stdout);
      if (venvCreate.stderr) console.error(venvCreate.stderr);
      
      if (!venvCreate.stdout.includes('VENV_CREATED')) {
        // Try without venv
        warn('Failed to create venv, checking for virtualenv ...');
        await sshExec(mainClient, 'pip3 install virtualenv 2>&1 || apt-get install -y python3-venv 2>&1');
        const venvCreate2 = await sshExec(mainClient,
          `cd ${MAIN_DIR} && python3 -m venv venv 2>&1 && echo "VENV_CREATED"`,
          { timeout: 120000 }
        );
        console.log(venvCreate2.stdout);
      }
      success('Virtual environment created');
    } else {
      success('Virtual environment already exists');
      // Update venv python path references if needed
      await sshExec(mainClient,
        `sed -i 's|/root/Personal-Wallet-Tele-Bot|/root/ACM-Personal-Wallet|g' ${MAIN_DIR}/venv/pyvenv.cfg 2>/dev/null; echo "venv cfg checked"`
      );
    }

    // Check for requirements.txt
    const reqCheck = await sshExec(mainClient, 
      `ls ${MAIN_DIR}/requirements.txt 2>/dev/null && echo "REQS_EXISTS" || echo "NO_REQS"`
    );
    console.log('requirements.txt check:', reqCheck.stdout.trim());

    if (reqCheck.stdout.includes('REQS_EXISTS')) {
      log('Installing Python dependencies ...');
      const installResult = await sshExec(mainClient,
        `cd ${MAIN_DIR} && source venv/bin/activate && pip install -r requirements.txt 2>&1 && echo "INSTALL_OK" || echo "INSTALL_FAILED"`,
        { timeout: 300000 }
      );
      console.log(installResult.stdout);
      if (installResult.stderr && !installResult.stderr.includes('WARNING')) {
        console.error('Pip STDERR:', installResult.stderr);
      }
      
      if (installResult.stdout.includes('INSTALL_OK')) {
        success('Python dependencies installed');
      } else {
        warn('Some dependencies may have failed to install — checking ...');
        // Retry with upgrade flag
        const retryResult = await sshExec(mainClient,
          `cd ${MAIN_DIR} && source venv/bin/activate && pip install --upgrade -r requirements.txt 2>&1 && echo "INSTALL_OK"`,
          { timeout: 300000 }
        );
        console.log(retryResult.stdout);
      }
    } else {
      warn('No requirements.txt found — checking for alternative dependency files ...');
      const altCheck = await sshExec(mainClient, `ls ${MAIN_DIR}/*.txt ${MAIN_DIR}/Pipfile ${MAIN_DIR}/setup.py ${MAIN_DIR}/pyproject.toml 2>/dev/null || echo "NO_DEPS"`);
      console.log(altCheck.stdout);
    }
    results.push({ step: '4-python-setup', status: 'success' });

    // ─── Systemd Service ────────────────────────────────────────────────────
    log('STEP 4b: Creating systemd service ...');

    // Check for existing start script or main entry point
    const scriptCheck = await sshExec(mainClient,
      `ls ${MAIN_DIR}/start_wallet_bot.sh ${MAIN_DIR}/start.sh ${MAIN_DIR}/run.sh ${MAIN_DIR}/bot.py ${MAIN_DIR}/main.py ${MAIN_DIR}/app.py 2>/dev/null || echo "NO_SCRIPTS_FOUND"`
    );
    console.log('Script check:', scriptCheck.stdout.trim());

    // Find the main Python file
    const pyMainCheck = await sshExec(mainClient,
      `ls ${MAIN_DIR}/*.py 2>/dev/null | head -10`
    );
    console.log('Python files:', pyMainCheck.stdout.trim());

    // Check existing start_wallet_bot.sh content
    let startScriptContent = '';
    const startScriptCheck = await sshExec(mainClient,
      `cat ${MAIN_DIR}/start_wallet_bot.sh 2>/dev/null || cat ${MAIN_DIR}/start.sh 2>/dev/null || echo "NO_START_SCRIPT"`
    );
    startScriptContent = startScriptCheck.stdout;
    console.log('Start script content:\n', startScriptContent.substring(0, 500));

    // Determine the main bot entry point
    let workingDir = MAIN_DIR;
    let execStart = '';
    
    // Look for the actual bot entry point
    const findMain = await sshExec(mainClient,
      `grep -l "Application\|bot = Application\|Updater\|Dispatcher\|asyncio.run\|if __name__" ${MAIN_DIR}/*.py 2>/dev/null | head -5`
    );
    console.log('Potential main files:', findMain.stdout.trim());

    // Prioritize known names
    const knownMains = ['bot.py', 'main.py', 'app.py', 'wallet_bot.py', 'telegram_bot.py'];
    let mainPyFile = '';
    for (const f of knownMains) {
      const check = await sshExec(mainClient, `test -f ${MAIN_DIR}/${f} && echo "FOUND" || echo ""`);
      if (check.stdout.trim() === 'FOUND') {
        mainPyFile = f;
        break;
      }
    }
    
    if (!mainPyFile) {
      // Pick first .py file from the grep results
      const lines = findMain.stdout.trim().split('\n').filter(l => l);
      if (lines.length > 0) {
        mainPyFile = path.basename(lines[0]);
      } else {
        // Find any .py file
        const anyPy = await sshExec(mainClient, `ls ${MAIN_DIR}/*.py 2>/dev/null | head -1`);
        const anyPyLine = anyPy.stdout.trim();
        if (anyPyLine) {
          mainPyFile = path.basename(anyPyLine);
        }
      }
    }
    
    log(`Detected main Python file: ${mainPyFile}`);

    execStart = `/bin/bash -c 'cd ${workingDir} && source venv/bin/activate && python3 ${mainPyFile}'`;

    // Also check if there's a shell script we should use
    if (startScriptContent && !startScriptContent.includes('NO_START_SCRIPT')) {
      // Update the start script content with new paths
      await sshExec(mainClient,
        `sed -i 's|/root/Personal-Wallet-Tele-Bot|/root/ACM-Personal-Wallet|g' ${MAIN_DIR}/start_wallet_bot.sh ${MAIN_DIR}/start.sh 2>/dev/null; echo "scripts updated"`
      );
      
      // If start_wallet_bot.sh exists, use it
      const useScript = await sshExec(mainClient, `test -f ${MAIN_DIR}/start_wallet_bot.sh && echo "EXISTS"`);
      if (useScript.stdout.includes('EXISTS')) {
        execStart = `/bin/bash ${MAIN_DIR}/start_wallet_bot.sh`;
      } else {
        const useAltScript = await sshExec(mainClient, `test -f ${MAIN_DIR}/start.sh && echo "EXISTS"`);
        if (useAltScript.stdout.includes('EXISTS')) {
          execStart = `/bin/bash ${MAIN_DIR}/start.sh`;
        }
      }
    }

    // Check for .env file
    const envCheck = await sshExec(mainClient, `ls ${MAIN_DIR}/.env 2>/dev/null && echo "ENV_EXISTS" || echo "NO_ENV"`);
    const hasEnv = envCheck.stdout.includes('ENV_EXISTS');

    // Create systemd service file
    const serviceContent = `[Unit]
Description=ACM's Personal Wallet Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${workingDir}
ExecStart=${execStart}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}
${hasEnv ? `EnvironmentFile=${MAIN_DIR}/.env` : ''}

# Security hardening
NoNewPrivileges=no
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
`;

    // Write service file
    log('Writing systemd service file ...');
    const writeService = await sshExec(mainClient,
      `cat > ${SERVICE_PATH} << 'SERVICEEOF'
${serviceContent}
SERVICEEOF
echo "SERVICE_WRITTEN" && cat ${SERVICE_PATH}`
    );
    console.log(writeService.stdout);
    
    if (!writeService.stdout.includes('SERVICE_WRITTEN')) {
      throw new Error('Failed to write service file');
    }
    success('Systemd service file created');

    // Enable and start the service
    log('Enabling and starting the service ...');
    const svcResult = await sshExec(mainClient,
      `systemctl daemon-reload 2>&1 && systemctl enable ${SERVICE_NAME} 2>&1 && systemctl start ${SERVICE_NAME} 2>&1 && echo "SERVICE_STARTED"`,
      { timeout: 60000 }
    );
    console.log(svcResult.stdout);
    if (svcResult.stderr) console.error('Systemctl stderr:', svcResult.stderr);

    if (svcResult.stdout.includes('SERVICE_STARTED')) {
      success('Service enabled and started');
    } else {
      warn('Service start may have issues — trying again ...');
      const retrySvc = await sshExec(mainClient,
        `systemctl start ${SERVICE_NAME} 2>&1 && echo "SERVICE_STARTED" || echo "SERVICE_FAILED"`,
        { timeout: 30000 }
      );
      console.log(retrySvc.stdout);
      if (retrySvc.stderr) console.error(retrySvc.stderr);
    }
    results.push({ step: '4-service-setup', status: 'success' });

    // ═══════════════════════════════════════════════════════════════════════════
    // STEP 5: Verify everything
    // ═══════════════════════════════════════════════════════════════════════════
    log('STEP 5: Verifying setup ...');

    // Check service status
    const statusResult = await sshExec(mainClient,
      `systemctl status ${SERVICE_NAME} --no-pager -l 2>&1`,
      { timeout: 15000 }
    );
    console.log('Service Status:');
    console.log(statusResult.stdout);
    results.push({ step: '5-service-status', status: 'success', output: statusResult.stdout.substring(0, 500) });

    // Check journal logs
    const journalResult = await sshExec(mainClient,
      `journalctl -u ${SERVICE_NAME} --no-pager -n 30 2>&1`,
      { timeout: 15000 }
    );
    console.log('Journal Logs:');
    console.log(journalResult.stdout);
    results.push({ step: '5-journal-logs', status: 'success' });

    // List final directory
    const finalLs = await sshExec(mainClient,
      `ls -la ${MAIN_DIR}/ && echo "---" && echo "Service file:" && cat ${SERVICE_PATH}`
    );
    console.log('Final directory listing & service file:');
    console.log(finalLs.stdout);
    results.push({ step: '5-final-listing', status: 'success' });

    // ═══════════════════════════════════════════════════════════════════════════
    // DONE
    // ═══════════════════════════════════════════════════════════════════════════
    console.log('\n' + '='.repeat(60));
    console.log('  MIGRATION COMPLETE');
    console.log('='.repeat(60));
    console.log(`  Source: ${SOURCE.host}:/root/Personal-Wallet-Tele-Bot`);
    console.log(`  Dest:   ${MAIN.host}:${MAIN_DIR}`);
    console.log(`  Service: ${SERVICE_NAME}`);
    console.log('='.repeat(60));

    return { success: true, results };

  } catch (err) {
    fail(`Migration failed: ${err.message}`);
    console.error(err);
    return { success: false, error: err.message, results };
  } finally {
    // Close connections
    if (sourceClient) { sourceClient.end(); }
    if (mainClient) { mainClient.end(); }
  }
}

// Run
main()
  .then((result) => {
    console.log('\nFINAL_RESULT:', JSON.stringify(result, null, 2));
    process.exit(result.success ? 0 : 1);
  })
  .catch((err) => {
    console.error('Unhandled error:', err);
    process.exit(1);
  });
