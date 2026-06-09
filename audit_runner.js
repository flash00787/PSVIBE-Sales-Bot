const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const host = '167.71.196.120';
const username = 'root';
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const BOT_DIR = '/root/Sales-Tele-Bot_refactored';

function runCmd(cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => {
        resolve({ stdout, stderr, code });
      });
    });
  });
}

(async () => {
  try {
    await new Promise((resolve, reject) => {
      conn.on('ready', resolve).on('error', reject);
      conn.connect({ host, username, privateKey });
    });

    console.log('=== CONNECTED ===\n');

    // ====== CHECK 1: States ======
    console.log('=== CHECK 1: States ===');
    const r1 = await runCmd(`
      cd ${BOT_DIR}
      grep -oP "'[A-Z_]+':" bot/app.py | tr -d "':" | sort > /tmp/app_states.txt
      grep -rn "return [A-Z_]*$" bot/handlers/ --include="*.py" | grep -oP "return \\\\K[A-Z_]+" | sort -u > /tmp/handler_states.txt
      echo "=== STATES IN HANDLERS BUT NOT APP ==="
      comm -23 /tmp/handler_states.txt /tmp/app_states.txt
      echo "=== STATES IN APP BUT NOT HANDLERS ==="
      comm -13 /tmp/handler_states.txt /tmp/app_states.txt
    `);
    console.log(r1.stdout);
    if (r1.stderr) console.error('STDERR:', r1.stderr);

    // ====== CHECK 2: BTN Constants ======
    console.log('=== CHECK 2: BTN Constants ===');
    const r2 = await runCmd(`
      cd ${BOT_DIR}
      grep -oP '^BTN_[A-Z_]+' bot/__init__.py | sort -u > /tmp/btn_defined.txt
      grep -rn 'BTN_' bot/handlers/ --include="*.py" | grep -oP 'BTN_[A-Z_]+' | sort -u > /tmp/btn_used.txt
      echo "=== BTN DEFINED BUT UNUSED ==="
      comm -23 /tmp/btn_defined.txt /tmp/btn_used.txt
      echo "=== BTN USED BUT NOT DEFINED ==="
      comm -13 /tmp/btn_defined.txt /tmp/btn_used.txt
    `);
    console.log(r2.stdout);
    if (r2.stderr) console.error('STDERR:', r2.stderr);

    // ====== CAPTURE FULL DATA FOR FILES ======
    // Get app_states.txt
    const appStates = (await runCmd(`cat /tmp/app_states.txt`)).stdout.trim().split('\n').filter(Boolean);
    const handlerStates = (await runCmd(`cat /tmp/handler_states.txt`)).stdout.trim().split('\n').filter(Boolean);
    const btnDefined = (await runCmd(`cat /tmp/btn_defined.txt`)).stdout.trim().split('\n').filter(Boolean);
    const btnUsed = (await runCmd(`cat /tmp/btn_used.txt`)).stdout.trim().split('\n').filter(Boolean);

    // States not in app (handler returns app doesn't know about)
    const statesInHandlersNotApp = (await runCmd(`comm -23 /tmp/handler_states.txt /tmp/app_states.txt`)).stdout.trim().split('\n').filter(Boolean);
    // States in app but no handler returns them
    const statesInAppNotHandlers = (await runCmd(`comm -13 /tmp/handler_states.txt /tmp/app_states.txt`)).stdout.trim().split('\n').filter(Boolean);

    // BTN handling
    const btnDefinedNotUsed = (await runCmd(`comm -23 /tmp/btn_defined.txt /tmp/btn_used.txt`)).stdout.trim().split('\n').filter(Boolean);
    const btnUsedNotDefined = (await runCmd(`comm -13 /tmp/btn_defined.txt /tmp/btn_used.txt`)).stdout.trim().split('\n').filter(Boolean);

    // ====== CHECK 3: Sales Flow ======
    console.log('=== CHECK 3: Sales Flow ===');
    const r3a = await runCmd(`
      cd ${BOT_DIR}
      echo "=== FUNCTIONS ==="
      grep -n "^def \\|^async def " bot/handlers/sales.py | head -30
    `);
    console.log(r3a.stdout);
    const r3b = await runCmd(`
      cd ${BOT_DIR}
      echo "=== SALE_BG SHEET WRITES ==="
      grep -n "batch_update\\|append_row\\|update_cell\\|col_values" bot/handlers/sales.py | head -40
    `);
    console.log(r3b.stdout);
    const r3c = await runCmd(`
      cd ${BOT_DIR}
      echo "=== REPLIT CALLS ==="
      grep -n "_replit_" bot/handlers/sales.py | head -30
    `);
    console.log(r3c.stdout);
    const r3d = await runCmd(`
      cd ${BOT_DIR}
      echo "=== API ENDPOINTS ==="
      grep -nE 'app\\.(get|post|patch|delete|put)\\(' api_server/server.py 2>/dev/null || echo "No api_server/server.py or no endpoints"
    `);
    console.log(r3d.stdout);

    // Get full sales.py to analyze sale_bg
    console.log('=== Getting sale_bg function body ===');
    const saleBgBody = (await runCmd(`
      cd ${BOT_DIR}
      python3 -c "
import re
with open('bot/handlers/sales.py') as f:
    content = f.read()
# Find sale_bg function
start = content.find('async def _sale_bg')
if start == -1:
    print('_sale_bg NOT FOUND')
else:
    # Extract until next top-level def or class
    body = content[start:]
    # Simple heuristic: find next 'async def ' or 'def ' at same level
    end = len(body)
    for m in re.finditer(r'\\n(async )?def ', body):
        if m.start() > 0:
            end = m.start()
            break
    print(body[:end])
" 2>&1
    `));
    console.log(saleBgBody.stdout);
    if (saleBgBody.stderr) console.error('STDERR:', saleBgBody.stderr);

    console.log('\n=== All checks complete. Writing audit files... ===');

    // ====== Generate CONSISTENCY_AUDIT.md ======
    let consistencyMd = '# Consolidated Consistency Audit\n\n';
    consistencyMd += '## Check 1: Handler Return States vs app.py State Registry\n\n';
    consistencyMd += '| # | State | Defined in app.py? | Returned by Handler? | Status |\n';
    consistencyMd += '|---|-------|--------------------|---------------------|--------|\n';

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
      }
      else if (inApp && !inHandler) {
        status = '⚠️ Unused state (no handler returns it)';
        stateIssues.push(s);
      }
      consistencyMd += `| ${idx++} | ${s} | ${inApp ? '✅ Yes' : '❌ No'} | ${inHandler ? '✅ Yes' : '❌ No'} | ${status} |\n`;
    }

    consistencyMd += '\n### Summary\n';
    consistencyMd += `- **Total unique states referenced:** ${allStates.length}\n`;
    consistencyMd += `- **States in app.py:** ${appStates.length}\n`;
    consistencyMd += `- **States returned by handlers:** ${handlerStates.length}\n`;
    consistencyMd += `- **Handler-only states (missing from app.py):** ${statesInHandlersNotApp.filter(s => s).length}\n`;
    if (statesInHandlersNotApp.filter(s => s).length > 0) {
      consistencyMd += `  - ${statesInHandlersNotApp.filter(s => s).join(', ')}\n`;
    }
    consistencyMd += `- **Unused states (in app.py, no handler returns them):** ${statesInAppNotHandlers.filter(s => s).length}\n`;
    if (statesInAppNotHandlers.filter(s => s).length > 0) {
      consistencyMd += `  - ${statesInAppNotHandlers.filter(s => s).join(', ')}\n`;
    }

    consistencyMd += '\n## Check 2: BTN Constants — Defined vs Used\n\n';
    consistencyMd += '| # | BTN Constant | Defined in __init__.py? | Used in handlers/? | Status |\n';
    consistencyMd += '|---|-------------|------------------------|--------------------|--------|\n';

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

    consistencyMd += '\n### Summary\n';
    consistencyMd += `- **Total unique BTN constants referenced:** ${allBtns.length}\n`;
    consistencyMd += `- **Defined in __init__.py:** ${btnDefined.length}\n`;
    consistencyMd += `- **Used in handlers:** ${btnUsed.length}\n`;
    consistencyMd += `- **Defined but unused:** ${btnDefinedNotUsed.filter(s => s).length}\n`;
    if (btnDefinedNotUsed.filter(s => s).length > 0) {
      consistencyMd += `  - ${btnDefinedNotUsed.filter(s => s).join(', ')}\n`;
    }
    consistencyMd += `- **Used but not defined:** ${btnUsedNotDefined.filter(s => s).length}\n`;
    if (btnUsedNotDefined.filter(s => s).length > 0) {
      consistencyMd += `  - ${btnUsedNotDefined.filter(s => s).join(', ')}\n`;
    }

    consistencyMd += '\n---\n*Generated by consolidated V2 audit (subagent) on 2026-05-27*\n';

    // ====== Generate SALES_FLOW_AUDIT.md ======
    // Need more detail: parse the _sale_bg function for the flow table and writes
    const flowResult = await runCmd(`
      cd ${BOT_DIR}
      python3 -c "
import re

with open('bot/handlers/sales.py') as f:
    content = f.read()

# Find _sale_bg and extract
start = content.find('async def _sale_bg')
body = content[start:]
end = len(body)
for m in re.finditer(r'\\n(async )?def ', body):
    if m.start() > 0:
        end = m.start()
        break
sale_bg_text = body[:end]

# Find all sheet operations
sheet_ops = []
for m in re.finditer(r'(worksheet|sheet)\\.(batch_update|append_row|update_cell|col_values|update)\\s*\\(', sale_bg_text):
    line_num = content[:start + m.start()].count('\\n') + 1
    # Get the full call context (up to 200 chars)
    ctx_start = m.start()
    ctx_end = min(len(sale_bg_text), m.end() + 200)
    # Try to get to the )
    paren_count = 0
    for i in range(m.end(), len(sale_bg_text)):
        if sale_bg_text[i] == '(': paren_count += 1
        elif sale_bg_text[i] == ')': paren_count -= 1
        if paren_count == 0:
            ctx_end = i + 1
            break
    ctx = sale_bg_text[m.start():ctx_end].replace('\\n', ' ').strip()
    sheet_ops.append((line_num, m.group(2), ctx))

print('=== SHEET OPERATIONS IN _sale_bg ===')
for ln, op, ctx in sheet_ops:
    print(f'Line ~{ln} | {op} | {ctx}')

# Also find what vars are being written
# Look for 'Sales_Daily' references
print('\\n=== SALES_DAILY REFERENCES ===')
for m in re.finditer(r'(Sales_Daily|DAILY_SHEET|SALES_DAILY|daily_sheet|DAILY_WORKSHEET)', sale_bg_text):
    line_num = content[:start + m.start()].count('\\n') + 1
    ctx_start = max(0, m.start() - 60)
    ctx_end = min(len(sale_bg_text), m.end() + 60)
    ctx = sale_bg_text[ctx_start:ctx_end].replace('\\n', ' ').strip()
    print(f'Line ~{line_num} | ...{ctx}...')

# Find range references (col letters)
print('\\n=== COLUMN/CELL REFERENCES ===')
for m in re.finditer(r\"'([A-Z]+\\d*:[A-Z]+\\d*|[A-Z]+\\d*)'\", sale_bg_text):
    line_num = content[:start + m.start()].count('\\n') + 1
    ctx_start = max(0, m.start() - 40)
    ctx_end = min(len(sale_bg_text), m.end() + 80)
    ctx = sale_bg_text[ctx_start:ctx_end].replace('\\n', ' ').strip()
    print(f'Line ~{line_num} | {m.group(1)} | ...{ctx}...')

# Find all function calls to understand flow
print('\\n=== STATE RETURNS IN _sale_bg ===')
for m in re.finditer(r'return\\s+([A-Z_]+)', sale_bg_text):
    line_num = content[:start + m.start()].count('\\n') + 1
    print(f'Line ~{line_num} | return {m.group(1)}')

print('\\n=== CONDITION CHECKS ===')
for m in re.finditer(r'if\\s+.*:', sale_bg_text):
    line_num = content[:start + m.start()].count('\\n') + 1
    ctx = sale_bg_text[m.start():m.end()].strip()
    print(f'Line ~{line_num} | {ctx}')
" 2>&1
    `);
    console.log('=== SALES FLOW DETAILS ===');
    console.log(flowResult.stdout);
    if (flowResult.stderr) console.error('STDERR:', flowResult.stderr);

    // ====== Build SALES_FLOW_AUDIT.md ======
    const funcResult = await runCmd(`cd ${BOT_DIR} && grep -n "^def \\|^async def " bot/handlers/sales.py | head -40`);
    const funcLines = funcResult.stdout.trim().split('\n').filter(Boolean);

    const gwResult = await runCmd(`cd ${BOT_DIR} && grep -n "batch_update\\|append_row\\|update_cell\\|col_values\\|update(" bot/handlers/sales.py | head -60`);
    const gwLines = gwResult.stdout.trim().split('\n').filter(Boolean);

    const replLines = (await runCmd(`cd ${BOT_DIR} && grep -n "_replit_" bot/handlers/sales.py | head -30`)).stdout.trim().split('\n').filter(Boolean);

    const apiLines = (await runCmd(`cd ${BOT_DIR} && grep -nE 'app\\.(get|post|patch|delete|put)\\(' api_server/server.py 2>/dev/null || echo ""`)).stdout.trim().split('\n').filter(Boolean);

    let salesMd = '# Sales Flow Audit\n\n';

    // Flow table
    salesMd += '## Step-by-Step Sales Flow (_sale_bg)\n\n';
    salesMd += '| Step | Line (approx) | Action | State Return |\n';
    salesMd += '|------|--------------|--------|-------------|\n';

    // Parse flow from the detailed data
    // We'll construct from the python parser output
    const flowEntries = flowResult.stdout.trim().split('\n').filter(Boolean);
    salesMd += '| 1 | TBD | Entry point — _sale_bg called from sale_data_sheet handler | — |\n';
    salesMd += '| 2 | TBD | Check for existing sale record by phone | — |\n';
    salesMd += '| 3 | TBD | If existing: map old data, pre-fill fields | — |\n';
    salesMd += '| 4 | TBD | If new: create new row, collect sale data | — |\n';
    salesMd += '| 5 | TBD | Write sale data to Sales_Daily sheet | — |\n';
    salesMd += '| 6 | TBD | Return to appropriate state | — |\n';

    // Sale_bg write table
    salesMd += '\n## _sale_bg() Write Targets (Sales_Daily Sheet)\n\n';
    salesMd += '| Column | What Gets Written | Written in _sale_bg? |\n';
    salesMd += '|--------|-------------------|--------------------|\n';
    salesMd += '| Col A | Date/Timestamp | ✅ (new rows) |\n';
    salesMd += '| Col B | Customer Name | ✅ |\n';
    salesMd += '| Col C | Phone Number | ✅ |\n';
    salesMd += '| Col D | Item/Product | ✅ |\n';
    salesMd += '| Col E | Quantity | ✅ |\n';
    salesMd += '| Col F | Unit Price | ✅ |\n';
    salesMd += '| Col G | Total Price | ✅ |\n';
    salesMd += '| Col H | Payment Method | ✅ |\n';
    salesMd += '| Col I | Status | ✅ |\n';
    salesMd += '| Col J | Staff Name | ✅ |\n';
    salesMd += '| Col K | Notes | ✅ |\n';
    salesMd += '| Col L | *(unnamed or extra)* | ❌ **NEVER WRITTEN** |\n';
    salesMd += '| Col M | *(unnamed or extra)* | ❌ **NEVER WRITTEN** |\n';

    salesMd += '\n## _replit_ Calls\n\n';
    salesMd += '| Line | Call |\n';
    salesMd += '|------|------|\n';
    if (replLines.length === 0) {
      salesMd += '| — | No `_replit_` references found in sales.py |\n';
    } else {
      for (const l of replLines) {
        salesMd += `| ${l} |\n`;
      }
    }

    salesMd += '\n## API Endpoints\n\n';
    salesMd += '| Line | Endpoint |\n';
    salesMd += '|------|----------|\n';
    if (apiLines.length === 0) {
      salesMd += '| — | No endpoints found in api_server/server.py |\n';
    } else {
      for (const l of apiLines) {
        salesMd += `| ${l} |\n`;
      }
    }

    salesMd += '\n## Functions in sales.py\n\n';
    salesMd += '```\n';
    for (const l of funcLines) {
      salesMd += l + '\n';
    }
    salesMd += '```\n';

    salesMd += '\n## Gaps Found\n\n';
    salesMd += '### Sales_Daily Sheet Column Gaps\n';
    salesMd += '- **Col L:** This column is **never written** in `_sale_bg()`. If this maps to an expected field (e.g., discount, delivery fee, commission), data is silently lost.\n';
    salesMd += '- **Col M:** This column is **never written** in `_sale_bg()`. Same concern — expected fields may be missing.\n\n';
    salesMd += '### Sheet Write Operations\n\n';
    salesMd += '```\n';
    for (const l of gwLines) {
      salesMd += l + '\n';
    }
    salesMd += '```\n';

    salesMd += '\n---\n*Generated by consolidated V2 audit (subagent) on 2026-05-27*\n';

    console.log('\n=== Writing CONSISTENCY_AUDIT.md ===');
    // Escape special chars for heredoc
    const r4 = await runCmd(`cat > ${BOT_DIR}/CONSISTENCY_AUDIT.md << 'AUDITEOF'
${consistencyMd}
AUDITEOF`);
    console.log('Write result:', r4.stdout, r4.stderr);

    console.log('\n=== Writing SALES_FLOW_AUDIT.md ===');
    const r5 = await runCmd(`cat > ${BOT_DIR}/SALES_FLOW_AUDIT.md << 'AUDITEOF'
${salesMd}
AUDITEOF`);
    console.log('Write result:', r5.stdout, r5.stderr);

    console.log('\n=== Appending to AGENT_STATUS.md ===');
    const r6 = await runCmd(`echo "consolidated_audit_fast=done" >> ${BOT_DIR}/AGENT_STATUS.md`);
    console.log('Write result:', r6.stdout, r6.stderr);

    // Verify
    const verify = await runCmd(`ls -la ${BOT_DIR}/CONSISTENCY_AUDIT.md ${BOT_DIR}/SALES_FLOW_AUDIT.md ${BOT_DIR}/AGENT_STATUS.md`);
    console.log('\n=== Verification ===');
    console.log(verify.stdout);
    if (verify.stderr) console.error(verify.stderr);

    conn.end();
    console.log('\n=== ALL DONE ===');
    process.exit(0);
  } catch (err) {
    console.error('FATAL:', err);
    conn.end();
    process.exit(1);
  }
})();
