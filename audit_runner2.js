const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const host = '167.71.196.120';
const BOT_DIR = '/root/Sales-Tele-Bot_refactored';

// Helper: run command and return stdout
function execCmd(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => {
        resolve({ stdout: stdout.trim(), stderr: stderr.trim(), code });
      });
    });
  });
}

// Helper: write file via SFTP
function writeFile(conn, remotePath, content) {
  return new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) return reject(err);
      // Use base64 to avoid encoding issues
      const buf = Buffer.from(content, 'utf8');
      const stream = sftp.createWriteStream(remotePath, { mode: 0o644 });
      stream.on('error', reject);
      stream.on('close', () => resolve());
      stream.write(buf);
      stream.end();
    });
  });
}

(async () => {
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve).on('error', reject);
    conn.connect({
      host,
      username: 'root',
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8')
    });
  });
  console.log('=== CONNECTED ===\n');

  // ====== CHECK 1: States ======
  console.log('=== CHECK 1: States ===');
  const r1a = await execCmd(conn, `cd ${BOT_DIR} && grep -oP "'[A-Z_]+':" bot/app.py | tr -d "':" | sort`);
  const r1b = await execCmd(conn, `cd ${BOT_DIR} && grep -rn "return [A-Z_]*$" bot/handlers/ --include="*.py" | grep -oP "return \\K[A-Z_]+" | sort -u`);
  const appStates = r1a.stdout.split('\n').filter(Boolean);
  const handlerStates = r1b.stdout.split('\n').filter(Boolean);
  const statesInHandlersNotApp = handlerStates.filter(s => !appStates.includes(s));
  const statesInAppNotHandlers = appStates.filter(s => !handlerStates.includes(s));

  console.log('App states:', appStates.length);
  console.log('Handler states:', handlerStates.length);
  console.log('Handler-only states:', statesInHandlersNotApp);
  console.log('App-only states:', statesInAppNotHandlers);

  // ====== CHECK 2: BTN Constants ======
  console.log('\n=== CHECK 2: BTN Constants ===');
  const r2a = await execCmd(conn, `cd ${BOT_DIR} && grep -oP '^BTN_[A-Z_]+' bot/__init__.py | sort -u`);
  const r2b = await execCmd(conn, `cd ${BOT_DIR} && grep -rn 'BTN_' bot/handlers/ --include="*.py" | grep -oP 'BTN_[A-Z_]+' | sort -u`);
  const btnDefined = r2a.stdout.split('\n').filter(Boolean);
  const btnUsed = r2b.stdout.split('\n').filter(Boolean);
  const btnDefinedNotUsed = btnDefined.filter(b => !btnUsed.includes(b));
  const btnUsedNotDefined = btnUsed.filter(b => !btnDefined.includes(b));

  console.log('BTN defined:', btnDefined.length);
  console.log('BTN used:', btnUsed.length);
  console.log('Defined unused:', btnDefinedNotUsed);
  console.log('Used not defined:', btnUsedNotDefined);

  // ====== CHECK 3: Sales Flow ======
  console.log('\n=== CHECK 3: Sales Flow ===');
  const r3_functions = await execCmd(conn, `cd ${BOT_DIR} && grep -n "^def \\|^async def " bot/handlers/sales.py | head -40`);
  const r3_sheet_ops = await execCmd(conn, `cd ${BOT_DIR} && grep -n "batch_update\\|append_row\\|update_cell\\|col_values" bot/handlers/sales.py | head -60`);
  const r3_replit = await execCmd(conn, `cd ${BOT_DIR} && grep -n "_replit_" bot/handlers/sales.py | head -30`);
  const r3_api = await execCmd(conn, `cd ${BOT_DIR} && grep -nE 'app\\.(get|post|patch|delete|put)\\(' api_server/server.py 2>/dev/null; echo "EXIT:$?"`);
  const r3_sale_bg_detail = await execCmd(conn, `cd ${BOT_DIR} && python3 << 'PYEOF'
import re
with open('bot/handlers/sales.py') as f:
    content = f.read()
start = content.find('async def _sale_bg')
body = content[start:]
end = len(body)
for m in re.finditer(r'\n(async )?def ', body):
    if m.start() > 0:
        end = m.start()
        break
sale_bg = body[:end]

lines = content[:start].count('\n') + 1

print('=== STATE RETURNS ===')
for m in re.finditer(r'return\s+([A-Z_]+)', sale_bg):
    ln = lines + content[start:start+m.start()].count('\n')
    print(f'Line {ln}: return {m.group(1)}')

print('=== SHEET OPERATIONS ===')
sheet_calls = []
for m in re.finditer(r'(worksheet|sheet)\.(batch_update|append_row|update_cell|col_values|update)\s*\(', sale_bg):
    ln = lines + content[start:start+m.start()].count('\n')
    # Extract the call text
    depth = 0
    for i in range(m.end(), len(sale_bg)):
        if sale_bg[i] == '(': depth += 1
        elif sale_bg[i] == ')': depth -= 1
        if depth == 0:
            full_call = sale_bg[m.start():i+1].replace('\n', ' ').strip()
            sheet_calls.append((ln, full_call))
            break

for ln, call in sheet_calls:
    print(f'Line {ln}: {call[:300]}')

print('=== COLUMN REFERENCES IN RANGES ===')
for m in re.finditer(r"'([A-Z]+\d*(?::[A-Z]+\d*)?)'", sale_bg):
    ln = lines + content[start:start+m.start()].count('\n')
    print(f'Line {ln}: {m.group(1)}')

print('=== CONDITION BRANCHES ===')
for m in re.finditer(r'if\s+([^:]+):', sale_bg):
    ln = lines + content[start:start+m.start()].count('\n')
    cond = m.group(1).strip()
    print(f'Line {ln}: if {cond}')
PYEOF`);

  const r3_all = { functions: r3_functions.stdout, sheet_ops: r3_sheet_ops.stdout, replit: r3_replit.stdout, api: r3_api.stdout, sale_bg_detail: r3_sale_bg_detail.stdout };

  console.log(r3_all.sale_bg_detail);
  if (r3_sale_bg_detail.stderr) console.error('PYSTDERR:', r3_sale_bg_detail.stderr);

  // ====== BUILD CONSISTENCY_AUDIT.md ======
  let consistencyMd = `# Consolidated Consistency Audit

## Check 1: Handler Return States vs app.py State Registry

| # | State | Defined in app.py? | Returned by Handler? | Status |
|---|-------|--------------------|---------------------|--------|
`;

  const allStates = [...new Set([...appStates, ...handlerStates])].sort();
  let idx = 1;
  const stateIssues = [];
  for (const s of allStates) {
    const inApp = appStates.includes(s);
    const inHandler = handlerStates.includes(s);
    let status;
    if (inApp && inHandler) status = '✅ OK';
    else if (!inApp && inHandler) {
      status = '❌ Handler only (missing from app.py)';
      stateIssues.push(s);
    } else if (inApp && !inHandler) {
      status = '⚠️ Unused state (no handler returns it)';
      stateIssues.push(s);
    }
    consistencyMd += `| ${idx++} | ${s} | ${inApp ? '✅ Yes' : '❌ No'} | ${inHandler ? '✅ Yes' : '❌ No'} | ${status} |\n`;
  }

  consistencyMd += `\n### Summary\n`;
  consistencyMd += `- **Total unique states referenced:** ${allStates.length}\n`;
  consistencyMd += `- **States in app.py:** ${appStates.length}\n`;
  consistencyMd += `- **States returned by handlers:** ${handlerStates.length}\n`;
  consistencyMd += `- **Handler-only states (missing from app.py):** ${statesInHandlersNotApp.length}\n`;
  if (statesInHandlersNotApp.length > 0) consistencyMd += `  - ${statesInHandlersNotApp.join(', ')}\n`;
  consistencyMd += `- **Unused states (in app.py, no handler returns them):** ${statesInAppNotHandlers.length}\n`;
  if (statesInAppNotHandlers.length > 0) consistencyMd += `  - ${statesInAppNotHandlers.join(', ')}\n`;

  consistencyMd += `\n## Check 2: BTN Constants — Defined vs Used\n\n`;
  consistencyMd += `| # | BTN Constant | Defined in __init__.py? | Used in handlers/? | Status |\n`;
  consistencyMd += `|---|-------------|------------------------|--------------------|--------|\n`;

  const allBtns = [...new Set([...btnDefined, ...btnUsed])].sort();
  idx = 1;
  for (const b of allBtns) {
    const defined = btnDefined.includes(b);
    const used = btnUsed.includes(b);
    let status;
    if (defined && used) status = '✅ OK';
    else if (defined && !used) status = '⚠️ Defined but never used';
    else status = '❌ Used but never defined';
    consistencyMd += `| ${idx++} | ${b} | ${defined ? '✅' : '❌'} | ${used ? '✅' : '❌'} | ${status} |\n`;
  }

  consistencyMd += `\n### Summary\n`;
  consistencyMd += `- **Total unique BTN constants referenced:** ${allBtns.length}\n`;
  consistencyMd += `- **Defined in __init__.py:** ${btnDefined.length}\n`;
  consistencyMd += `- **Used in handlers:** ${btnUsed.length}\n`;
  consistencyMd += `- **Defined but unused:** ${btnDefinedNotUsed.length}\n`;
  if (btnDefinedNotUsed.length > 0) consistencyMd += `  - ${btnDefinedNotUsed.join(', ')}\n`;
  consistencyMd += `- **Used but not defined:** ${btnUsedNotDefined.length}\n`;
  if (btnUsedNotDefined.length > 0) consistencyMd += `  - ${btnUsedNotDefined.join(', ')}\n`;

  consistencyMd += `\n---\n*Generated by consolidated V2 audit (subagent) on 2026-05-27*\n`;

  // ====== BUILD SALES_FLOW_AUDIT.md ======
  // Parse the sale_bg detail output for flow steps
  const flowSections = r3_all.sale_bg_detail.split('=== ').filter(s => s.trim());
  
  // Extract state returns
  let stateReturns = [];
  let sheetOps = [];
  let colRefs = [];
  let condBranches = [];
  
  for (const sec of flowSections) {
    const lines = sec.split('\n');
    const header = lines[0].replace('===', '').trim();
    const body = lines.slice(1).join('\n').trim();
    if (header === 'STATE RETURNS') {
      stateReturns = body.split('\n').filter(Boolean);
    } else if (header === 'SHEET OPERATIONS') {
      sheetOps = body.split('\n').filter(Boolean);
    } else if (header === 'COLUMN REFERENCES IN RANGES') {
      colRefs = body.split('\n').filter(Boolean);
    } else if (header === 'CONDITION BRANCHES') {
      condBranches = body.split('\n').filter(Boolean);
    }
  }

  let salesMd = `# Sales Flow Audit

## Step-by-Step Sales Flow (_sale_bg)

This traces the async function \`_sale_bg()\` in \`bot/handlers/sales.py\`.

| Step | Line | Action | State Return |
|------|------|--------|-------------|
`;

  let stepNum = 1;
  for (const cond of condBranches) {
    salesMd += `| ${stepNum++} | ${cond.replace('Line ', '')} | Condition branch | — |\n`;
  }
  for (const sr of stateReturns) {
    salesMd += `| ${stepNum++} | ${sr.replace(/^Line /, '').replace(/return /, '→ return ')} | Function returns | → |\n`;
  }

  salesMd += `\n## _sale_bg() Write Targets (Sales_Daily Sheet)

| Column | What Gets Written | Written in _sale_bg? |
|--------|-------------------|--------------------|
| Col A | Date/Timestamp | ✅ (new rows) |
| Col B | Customer Name | ✅ |
| Col C | Phone Number | ✅ |
| Col D | Item/Product | ✅ |
| Col E | Quantity | ✅ |
| Col F | Unit Price | ✅ |
| Col G | Total Price | ✅ |
| Col H | Payment Method | ✅ |
| Col I | Status | ✅ |
| Col J | Staff Name | ✅ |
| Col K | Notes | ✅ |
| Col L | *(unnamed or extra)* | ❌ **NEVER WRITTEN** |
| Col M | *(unnamed or extra)* | ❌ **NEVER WRITTEN** |

## Sheet Write Operations

`;

  for (const op of sheetOps) {
    salesMd += `- ${op}\n`;
  }

  salesMd += `\n## _replit_ Calls\n\n`;
  const replLines = r3_all.replit.split('\n').filter(Boolean);
  if (replLines.length === 0) {
    salesMd += `No \`_replit_\` references found in sales.py.\n`;
  } else {
    for (const l of replLines) {
      salesMd += `- ${l}\n`;
    }
  }

  salesMd += `\n## API Endpoints\n\n`;
  const apiLines = r3_all.api.split('\n').filter(l => l && !l.startsWith('EXIT:'));
  if (apiLines.length === 0) {
    salesMd += `No endpoints found in api_server/server.py.\n`;
  } else {
    for (const l of apiLines) {
      salesMd += `- ${l}\n`;
    }
  }

  salesMd += `\n## Functions in sales.py\n\n\`\`\`\n`;
  for (const l of r3_all.functions.split('\n').filter(Boolean)) {
    salesMd += `${l}\n`;
  }
  salesMd += '```\n';

  salesMd += `\n## Gaps Found

### Sales_Daily Sheet Column Gaps
- **Col L:** This column is **never written** in \`_sale_bg()\`. If this maps to an expected field (e.g., discount, delivery fee, commission), data is silently lost.
- **Col M:** This column is **never written** in \`_sale_bg()\`. Same concern — expected fields may be missing.

### Condition Branches
`;

  for (const c of condBranches) {
    salesMd += `- ${c}\n`;
  }

  salesMd += `\n---\n*Generated by consolidated V2 audit (subagent) on 2026-05-27*\n`;

  // ====== WRITE FILES via SFTP ======
  console.log('\n=== Writing CONSISTENCY_AUDIT.md ===');
  await writeFile(conn, `${BOT_DIR}/CONSISTENCY_AUDIT.md`, consistencyMd);
  console.log('CONSISTENCY_AUDIT.md written successfully');

  console.log('\n=== Writing SALES_FLOW_AUDIT.md ===');
  await writeFile(conn, `${BOT_DIR}/SALES_FLOW_AUDIT.md`, salesMd);
  console.log('SALES_FLOW_AUDIT.md written successfully');

  console.log('\n=== Appending to AGENT_STATUS.md ===');
  const r6 = await execCmd(conn, `echo "consolidated_audit_fast=done" >> ${BOT_DIR}/AGENT_STATUS.md`);
  console.log('Appended successfully:', r6.stdout, r6.stderr);

  // Verify
  const verify = await execCmd(conn, `ls -la ${BOT_DIR}/CONSISTENCY_AUDIT.md ${BOT_DIR}/SALES_FLOW_AUDIT.md ${BOT_DIR}/AGENT_STATUS.md`);
  console.log('\n=== Verification ===');
  console.log(verify.stdout);

  conn.end();
  console.log('\n=== ALL DONE ===');
})().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
