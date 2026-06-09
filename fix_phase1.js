const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '167.71.196.120';
const PORT = 22;
const USERNAME = 'root';
const PRIVATE_KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const V2_BASE = '/root/staging/bot_src/bot/handlers';

function sshExec(conn, cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    let stdout = '', stderr = '';
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ code, stdout, stderr });
      });
    });
  });
}

function connect() {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => resolve(conn));
    conn.on('error', reject);
    conn.connect({
      host: HOST,
      port: PORT,
      username: USERNAME,
      privateKey: fs.readFileSync(PRIVATE_KEY_PATH),
    });
  });
}

async function main() {
  const conn = await connect();
  console.log('=== STEP 1: Fix referral.py ===');
  
  // Read the first 15 lines of referral.py to confirm current state
  let r = await sshExec(conn, `head -15 ${V2_BASE}/referral.py`);
  console.log('BEFORE:', r.stdout.substring(0, 500));

  // Fix: Add 'from bot import *' at top, and add 'asyncio' to imports
  // Using sed to do a two-step fix on the staging file
  const fixReferral = `
    cd ${V2_BASE} && \
    cp referral.py referral.py.bak && \
    python3 -c "
import re
with open('referral.py', 'r') as f:
    content = f.read()

# Step 1: Add 'from bot import *' at the very top, before the docstring
content = 'from bot import *\\n' + content

# Step 2: Add 'asyncio' to the import line: 'import logging, re, json' -> 'import asyncio, logging, re, json'
content = content.replace(
    'import logging, re, json',
    'import asyncio, logging, re, json'
)

with open('referral.py', 'w') as f:
    f.write(content)
print('OK: referral.py fixed')
"
  `;
  r = await sshExec(conn, fixReferral);
  console.log('FIX referral:', r.stdout, r.stderr || '');

  // Verify fix
  r = await sshExec(conn, `head -12 ${V2_BASE}/referral.py`);
  console.log('AFTER:', r.stdout.substring(0, 500));

  // === STEP 2: Fix discount.py ===
  console.log('\n=== STEP 2: Fix discount.py ===');
  r = await sshExec(conn, `head -10 ${V2_BASE}/discount.py`);
  console.log('BEFORE:', r.stdout.substring(0, 400));

  const fixDiscount = `
    cd ${V2_BASE} && \
    cp discount.py discount.py.bak && \
    python3 -c "
with open('discount.py', 'r') as f:
    content = f.read()

# Step 1: Add 'from bot import *' at the very top
content = 'from bot import *\\n' + content

# Step 2: Add 'asyncio' to imports
content = content.replace(
    'import logging, re, json',
    'import asyncio, logging, re, json'
)

with open('discount.py', 'w') as f:
    f.write(content)
print('OK: discount.py fixed')
"
  `;
  r = await sshExec(conn, fixDiscount);
  console.log('FIX discount:', r.stdout, r.stderr || '');

  r = await sshExec(conn, `head -12 ${V2_BASE}/discount.py`);
  console.log('AFTER:', r.stdout.substring(0, 500));

  // === STEP 3: Syntax check all 4 files ===
  console.log('\n=== STEP 3: Syntax checks ===');
  for (const f of ['sales.py', 'members.py', 'referral.py', 'discount.py']) {
    r = await sshExec(conn, `cd ${V2_BASE} && python3 -c "import ast; ast.parse(open('${f}').read()); print('${f} OK')" 2>&1`);
    console.log(`${f}: ${r.stdout.trim() || r.stderr.trim()}`);
  }

  // === STEP 4: Check for additional issues — any uses of undefined symbols ===
  console.log('\n=== STEP 4: Check for non-bot imports that might be missing ===');
  // Check if asyncio is used anywhere beyond what we fixed
  r = await sshExec(conn, `grep -n "asyncio\\." ${V2_BASE}/sales.py | head -5`);
  console.log('sales.py asyncio usage:', r.stdout.substring(0, 300));
  r = await sshExec(conn, `grep -n "asyncio\\." ${V2_BASE}/members.py | head -5`);
  console.log('members.py asyncio usage:', r.stdout.substring(0, 300));
  // sales and members use from bot import *, which presumably imports asyncio

  conn.end();
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
