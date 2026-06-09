const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const VPS_HOST = '5.223.81.16';
const VPS_USER = 'root';
const KEY_PATH = path.resolve(__dirname, '..', '.ssh', 'id_rsa');
const BOT_DIR = '/opt/construction-bot';
const NEW_TOKEN = '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';
const NEW_URL = `https://${NEW_TOKEN}@github.com/flash00787/three_brothers_construction.git`;

const RESULT_FILE = path.resolve(__dirname, 'coco_pat_result.txt');

const results = [];
function log(msg, isError = false) {
    const prefix = isError ? '[ERROR]' : '[INFO]';
    const line = `${prefix} ${msg}`;
    results.push(line);
    console.log(line);
}

// Run command via SSH
function execCommand(conn, cmd) {
    return new Promise((resolve, reject) => {
        conn.exec(cmd, (err, stream) => {
            if (err) return reject(err);
            let stdout = '';
            let stderr = '';
            stream.on('data', (data) => { stdout += data.toString(); });
            stream.stderr.on('data', (data) => { stderr += data.toString(); });
            stream.on('close', (code) => {
                resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
            });
        });
    });
}

async function main() {
    log('=== Starting GitHub PAT Fix for Three Brothers Construction Bot ===');

    const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

    const conn = new Client();

    await new Promise((resolve, reject) => {
        conn.on('ready', () => {
            log('SSH connection established successfully');
            resolve();
        });
        conn.on('error', (err) => {
            reject(err);
        });
        conn.connect({
            host: VPS_HOST,
            username: VPS_USER,
            privateKey: privateKey
        });
    });

    try {
        // Step 1: Check current git remote
        log('Step 1: Checking current git remote...');
        const remoteResult = await execCommand(conn, `cd ${BOT_DIR} && git remote -v`);
        log(`Remote stdout:\n${remoteResult.stdout}`);
        if (remoteResult.stderr) log(`Remote stderr: ${remoteResult.stderr}`, true);
        if (remoteResult.code !== 0) log(`Remote exit code: ${remoteResult.code}`, true);

        // Step 2: Update remote URL
        log('Step 2: Updating remote URL with new PAT...');
        const setUrlResult = await execCommand(conn, `cd ${BOT_DIR} && git remote set-url origin ${NEW_URL}`);
        if (setUrlResult.code !== 0) {
            log(`Failed to set remote URL: ${setUrlResult.stderr}`, true);
        } else {
            log('Remote URL updated successfully');
        }

        // Verify new remote
        const verifyRemote = await execCommand(conn, `cd ${BOT_DIR} && git remote -v`);
        log(`Updated remote:\n${verifyRemote.stdout}`);

        // Step 3: Test fetch
        log('Step 3: Testing git fetch...');
        const fetchResult = await execCommand(conn, `cd ${BOT_DIR} && git fetch --dry-run 2>&1`);
        const fetchStdout = fetchResult.stdout + (fetchResult.stderr ? '\n' + fetchResult.stderr : '');
        log(`Fetch result:\n${fetchStdout}`);
        const fetchSuccess = fetchResult.code === 0;
        if (!fetchSuccess) log('FETCH FAILED', true);

        // Step 4: Check staged changes
        log('Step 4: Checking git status...');
        const statusResult = await execCommand(conn, `cd ${BOT_DIR} && git status`);
        log(`Status:\n${statusResult.stdout}`);
        if (statusResult.stderr) log(`Status stderr: ${statusResult.stderr}`);
        
        // Parse staged files
        const statusLines = statusResult.stdout.split('\n');
        const stagedFiles = [];
        let inChanges = false;
        for (const line of statusLines) {
            if (line.includes('Changes to be committed')) {
                inChanges = true;
                continue;
            }
            if (line.includes('Changes not staged') || line.includes('Untracked files')) {
                inChanges = false;
            }
            if (inChanges && line.trim().startsWith('modified:') || inChanges && line.trim().startsWith('new file:')) {
                stagedFiles.push(line.trim());
            }
        }

        // Step 5: Try push dry-run
        let pushSuccess = false;
        let pushOutput = '';
        if (fetchSuccess) {
            log('Step 5: Testing git push (dry-run)...');
            const pushResult = await execCommand(conn, `cd ${BOT_DIR} && git push origin main --dry-run 2>&1`);
            pushOutput = pushResult.stdout + (pushResult.stderr ? '\n' + pushResult.stderr : '');
            log(`Push result:\n${pushOutput}`);
            pushSuccess = pushResult.code === 0;
            if (!pushSuccess) log('PUSH DRY-RUN FAILED', true);
        } else {
            log('Step 5: Skipping push dry-run because fetch failed', true);
        }

        // Compile final report
        log('\n=== FINAL REPORT ===');
        log(`Fetch success: ${fetchSuccess ? 'YES' : 'NO'}`);
        log(`Push dry-run success: ${pushSuccess ? 'YES' : 'NO'}`);
        log(`Staged files (${stagedFiles.length}):`);
        stagedFiles.forEach(f => log(`  - ${f}`));
        if (stagedFiles.length === 0) log('  (none)');

        // Write result file
        const resultContent = results.join('\n') + '\n\n=== RESULT: ' + 
            (fetchSuccess ? 'OK' : 'ERROR: Fetch failed') + 
            ' ===\n';
        fs.writeFileSync(RESULT_FILE, resultContent);
        log(`Result written to ${RESULT_FILE}`);

    } catch (err) {
        const errorMsg = `Script error: ${err.message}`;
        log(errorMsg, true);
        const resultContent = results.join('\n') + `\n\n=== RESULT: ERROR: ${err.message} ===\n`;
        fs.writeFileSync(RESULT_FILE, resultContent);
    } finally {
        conn.end();
        log('SSH connection closed');
    }
}

main().catch(err => {
    console.error('Fatal:', err);
    const resultContent = results.join('\n') + `\n\n=== RESULT: ERROR: ${err.message} ===\n`;
    fs.writeFileSync(RESULT_FILE, resultContent);
    process.exit(1);
});
