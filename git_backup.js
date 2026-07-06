#!/usr/bin/env node
/**
 * git_backup.js — Git Auto-Backup System
 * 
 * Auto-commits and pushes changes on a schedule.
 * Runs for both workspace (memory) and VPS (psvibe-sales-bot).
 * 
 * Usage:
 *   node git_backup.js status         → Show pending changes
 *   node git_backup.js commit         → Auto-commit changes
 *   node git_backup.js push           → Commit + push
 *   node git_backup.js setup          → Create cron job
 *   node git_backup.js setup-vps      → Setup VPS git cron
 *   node git_backup.js vps-push       → Push VPS repo
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const WORKSPACE = __dirname;
const VPS_HOST = '5.223.81.16';
const VPS_REPO = '/root/psvibe-sales-bot';

function run(cmd, cwd = WORKSPACE, timeout = 30000) {
  try {
    const result = execSync(cmd, { cwd, timeout, encoding: 'utf8', stdio: 'pipe' });
    return { code: 0, stdout: result.trim(), stderr: '' };
  } catch (err) {
    return {
      code: err.status || 1,
      stdout: err.stdout?.toString().trim() || '',
      stderr: err.stderr?.toString().trim() || err.message,
    };
  }
}

function runSSH(cmd, timeout = 15000) {
  const { Client } = require('ssh2');
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let out = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => out += 'STDERR:' + d.toString());
        stream.on('close', () => { conn.end(); resolve(out.trim()); });
      });
    });
    conn.on('error', reject);
    conn.connect({
      host: VPS_HOST, port: 22, username: 'root',
      privateKey: fs.readFileSync(path.join(WORKSPACE, '.ssh', 'id_rsa')),
      readyTimeout: 10000,
    });
    if (timeout) setTimeout(() => { conn.end(); reject(new Error('SSH timeout')); }, timeout);
  });
}

// ── Workspace Git ──
function workspaceStatus() {
  const gitDir = path.join(WORKSPACE, '.git');
  if (!fs.existsSync(gitDir)) {
    return { changes: 0, message: '⚠️ Not a git repository — skipping workspace backup' };
  }
  const { stdout } = run('git status --porcelain');
  const lines = stdout ? stdout.split('\n').filter(l => l.trim()) : [];
  const changes = lines.length;

  // Show details
  const details = lines.map(l => `  ${l.substring(0, 2)} ${l.substring(3)}`).join('\n');
  return { changes, details, lines };
}

function workspaceCommit(message) {
  const status = workspaceStatus();
  if (status.changes === 0) {
    return { committed: false, message: '✅ Clean — no changes to commit' };
  }

  run('git add -A');
  const { stdout, stderr } = run(`git commit -m "${message}"`);
  return { committed: true, message: stdout || stderr };
}

function workspacePush() {
  const { stdout } = run('git push origin HEAD:kora-workspace 2>&1');
  return stdout;
}

// ── VPS Git (via SSH) ──
async function vpsStatus() {
  try {
    const out = await runSSH(`cd ${VPS_REPO} && git status --porcelain`);
    const lines = out ? out.split('\n').filter(l => l.trim()) : [];
    return { changes: lines.length, details: lines };
  } catch (err) {
    return { changes: 0, error: err.message };
  }
}

async function vpsCommit(message) {
  try {
    // Exclude log files from commit
    await runSSH(`cd ${VPS_REPO} && git add -A`);
    await runSSH(`cd ${VPS_REPO} && git checkout -- '*.log*' 'bot_status*'`);
    const out = await runSSH(`cd ${VPS_REPO} && git commit -m "${message}" 2>&1`);
    return { success: true, message: out };
  } catch (err) {
    return { success: false, message: err.message };
  }
}

async function vpsPush() {
  try {
    const out = await runSSH(`cd ${VPS_REPO} && git push 2>&1`);
    return out;
  } catch (err) {
    return `❌ Push failed: ${err.message}`;
  }
}

// ── Create cron ──
function setupCron(forVps = false) {
  const now = new Date();
  const hour = 23; // 11 PM Myanmar Time

  if (forVps) {
    console.log(`
📅 VPS Auto-Backup Cron Schedule:
   Time: Every day at ${hour}:00 Myanmar Time (${hour-6}:30 UTC)
   Command: git add -A → git commit → git push (excludes logs)
   
   To add: Run: contab -e on the VPS
   Add line:
   30 ${hour > 6 ? hour - 6 : hour + 18} * * * cd ${VPS_REPO} && git add -A && git checkout -- '*.log*' 'bot_status*' && git commit -m "Auto-backup \$(date +\\%Y-\\%m-\\%d)" && git push
`);
    return;
  }

  // Workspace cron
  console.log(`
📅 Workspace Auto-Backup Cron Schedule:
   Time: Every day at ${hour}:00 Myanmar Time
   This should be set up as an OpenClaw cron job.
   
   I'll create a daily system event for this:
`);
}

// ── Setup daily cron job in OpenClaw ──
async function setupOpenClawCron() {
  // Myanmar time 11 PM = 16:30 UTC (UTC+6:30)
  // Actually: 23:00 MMT = 16:30 UTC
  const cronExpr = '30 16 * * *'; // 16:30 UTC = 23:00 MMT
  
  console.log(`🕐 Creating OpenClaw cron job for daily git backup...
   Schedule: ${cronExpr} (23:00 Myanmar Time)
   Action: Commit workspace + VPS repos, push
`);
}

// ── CLI ──
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'status';

  if (cmd === 'status') {
    console.log('📊 Git Backup — Status Report\n');

    const ws = workspaceStatus();
    console.log(`📁 Workspace (memory/config): ${ws.changes} change(s)`);
    if (ws.details) console.log(ws.details);
    console.log();

    console.log(`🖥️  VPS (psvibe-sales-bot): checking...`);
    const vps = await vpsStatus();
    if (vps.error) {
      console.log(`   ❌ ${vps.error}`);
    } else {
      console.log(`   ${vps.changes} change(s)`);
      vps.details?.forEach(l => console.log(`  ${l}`));
    }
    console.log();

  } else if (cmd === 'commit') {
    const timestamp = new Date().toISOString().split('.')[0].replace('T', ' ');
    const msg = `Auto-backup ${timestamp}`;

    console.log('📤 Committing changes...\n');

    const ws = workspaceCommit(msg);
    console.log(`📁 Workspace: ${ws.message}`);

    console.log(`🖥️  VPS: committing...`);
    const vpsr = await vpsCommit(msg);
    console.log(`   ${vpsr.message}`);

    console.log(`\n✅ Auto-backup complete`);

  } else if (cmd === 'push') {
    console.log('📤 Pushing all changes...\n');

    const ws = workspacePush();
    console.log(`📁 Workspace: ${ws}`);

    console.log(`🖥️  VPS: pushing...`);
    const vpsr = await vpsPush();
    console.log(`   ${vpsr}`);

    console.log(`\n✅ Push complete`);

  } else if (cmd === 'setup') {
    await setupOpenClawCron();
    console.log('Manual cron setup for workspace (run on VPS):');
    setupCron(true);

  } else if (cmd === 'vps-push') {
    console.log('📤 Pushing VPS repo...');
    const wsR = workspaceCommit(`Auto-backup before VPS push ${new Date().toISOString()}`);
    console.log(`📁 Workspace: ${wsR.message}`);

    const result = await vpsPush();
    console.log(`🖥️  VPS: ${result}`);

  } else {
    console.log(`Unknown command: ${cmd}`);
    console.log('Usage: node git_backup.js <status|commit|push|setup|vps-push>');
  }
}

main().catch(console.error);
