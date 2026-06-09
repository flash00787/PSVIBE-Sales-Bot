const fs = require('fs');
const path = require('path');

const auditDir = '/home/node/.openclaw/workspace/audit_split';

// 1. Load api_client.py — extract all api_* function names
const apiClientRaw = fs.readFileSync(path.join(auditDir, 'api_client.py'), 'utf8');
const apiClientFuncs = new Set();
const apiClientRegex = /^def (api_\w+)/gm;
let m;
while ((m = apiClientRegex.exec(apiClientRaw)) !== null) {
  apiClientFuncs.add(m[1]);
}

// Also extract the paths called inside _api_call
const apiClientEndpoints = new Set();
const endpointRegex = /_api_call\("(\w+)",\s*"([^"]+)"/g;
while ((m = endpointRegex.exec(apiClientRaw)) !== null) {
  apiClientEndpoints.add(`${m[1]} /api/${m[2].replace(/^\/+/,'')}`);
}

// 2. Load app.py — extract route/endpoint patterns and BTN_* constants
const appPyRaw = fs.readFileSync(path.join(auditDir, 'app.py'), 'utf8');

// Extract app.py endpoints (route decorators or API base path references)
const appEndpoints = new Set();
// Look for @app.route or similar
const routeRegex = /@app\.(?:route|get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]/g;
while ((m = routeRegex.exec(appPyRaw)) !== null) {
  appEndpoints.add(m[1]);
}

// Also look for api/ references in app.py 
const apiPathRegex = /["']\/api\/([^"']+)["']/g;
while ((m = apiPathRegex.exec(appPyRaw)) !== null) {
  appEndpoints.add('/api/' + m[1]);
}

// 3. Define handler files to check
const handlerFiles = [
  'handlers_booking.py',
  'handlers_booking_flow.py',
  'handlers_stock.py',
  'handlers_stock_in.py',
  'handlers_referral.py',
  'handlers_discount.py',
  'handlers_waitlist.py',
  'handlers_attendance.py',
  'handlers_broadcast.py',
  'handlers_notify.py',
  'handlers_games.py',
  'handlers_ssd_disc.py'
];

// 4. BTN_* constants — scan app.py for them
const btnMap = new Map();
const btnRegex = /^(\w+)\s*=\s*["'](.+?)["']/gm;
let appLine = 0;
const appLines = appPyRaw.split('\n');
for (let i = 0; i < appLines.length; i++) {
  const line = appLines[i];
  const bm = line.match(/^(\w+)\s*=\s*["'](.+?)["']/);
  if (bm && bm[1].startsWith('BTN_')) {
    btnMap.set(bm[1], bm[2]);
  }
}

// Also search in the actual bot state files
// BTN_* will be searched below from app.py

// Lets extract BTN_* from ALL files
const allBtnRefs = {};
handlerFiles.forEach(f => {
  const content = fs.readFileSync(path.join(auditDir, f), 'utf8');
  const lines = content.split('\n');
  const btnRefs = new Set();
  lines.forEach((line, i) => {
    const match = line.match(/\b(BTN_\w+)\b/g);
    if (match) match.forEach(b => btnRefs.add(b));
  });
  allBtnRefs[f] = [...btnRefs].sort();
});

// 5. Analyze each handler file
const results = [];

handlerFiles.forEach(f => {
  const content = fs.readFileSync(path.join(auditDir, f), 'utf8');
  const lines = content.split('\n');
  const fname = f.replace('handlers_', '').replace('.py', '');
  
  const entry = {
    file: f,
    display: `handlers/${fname}.py`,
    apiCalls: [],
    gspreadCalls: [],
    missingApiFuncs: [],
    btnRefs: allBtnRefs[f] || [],
    lineCount: lines.length
  };
  
  // Extract all api_* calls made in this handler
  const apiCallRegex = /(api_\w+)\s*\(/g;
  while ((m = apiCallRegex.exec(content)) !== null) {
    if (!entry.apiCalls.includes(m[1])) {
      entry.apiCalls.push(m[1]);
    }
  }
  
  // Check if each api_* function exists in api_client.py
  entry.apiCalls.forEach(call => {
    if (!apiClientFuncs.has(call)) {
      entry.missingApiFuncs.push(call);
    }
  });
  
  // Check for direct gspread calls
  const gsRegex = /(gc\.|gspread|\.worksheet|\.values_get|\.values_update|sheet\.append|sheet\.update|sheet\.get_all|sh\.worksheet|Spreadsheet)/g;
  while ((m = gsRegex.exec(content)) !== null) {
    const lineNum = content.substring(0, m.index).split('\n').length;
    const callLine = lines[lineNum-1]?.trim() || '';
    if (!entry.gspreadCalls.some(g => g.line === lineNum)) {
      entry.gspreadCalls.push({ line: lineNum, text: callLine });
    }
  }

  // Also check _replit_get, _replit_post etc (internal API wrappers)
  const replitRegex = /(_replit_\w+)\s*\(/g;
  entry.replitCalls = [];
  while ((m = replitRegex.exec(content)) !== null) {
    const callName = m[1];
    if (!entry.replitCalls.includes(callName)) entry.replitCalls.push(callName);
  }

  // Check for _api_call direct usage
  const directApiCallRegex = /_api_call\s*\(/g;
  entry.directApiCallCount = 0;
  let dc = 0;
  while ((m = directApiCallRegex.exec(content)) !== null) dc++;
  entry.directApiCallCount = dc;

  // Check for Mongo/DB references
  const dbRefs = new Set();
  const dbRegex = /\b(mongo|mongodb|collection\.|db\.|insert_one|find_one|update_one|delete_one)\b/gi;
  while ((m = dbRegex.exec(content)) !== null) {
    dbRefs.add(m[1].toLowerCase());
  }
  entry.dbRefs = [...dbRefs];

  results.push(entry);
});

// === OUTPUT ===
let output = `# Audit Report: Booking/Stock/Other Handlers
**Generated:** ${new Date().toISOString()}
**Source:** /root/psvibe-sales-bot/bot/

---

## api_client.py — API Functions Available (${apiClientFuncs.size} total)

\`\`\`
${[...apiClientFuncs].sort().join('\n')}
\`\`\`

### Endpoints registered in api_client.py:
\`\`\`
${[...apiClientEndpoints].sort().join('\n')}
\`\`\`

---

## app.py — Route/Endpoint References Found

\`\`\`
${[...appEndpoints].sort().join('\n')}
\`\`\`

---

## Handler-by-Handler Analysis

`;

results.forEach(r => {
  output += `\n## ${r.display}\n\n`;
  output += `- **Lines:** ${r.lineCount}\n`;
  
  output += `\n### 1. api_* calls made (${r.apiCalls.length} unique):\n`;
  if (r.apiCalls.length === 0) {
    output += `None found.\n`;
  } else {
    r.apiCalls.sort().forEach(c => {
      const exists = apiClientFuncs.has(c) ? '✅ EXISTS' : '❌ MISSING';
      output += `- \`${c}()\` — ${exists}\n`;
    });
  }
  
  if (r.missingApiFuncs.length > 0) {
    output += `\n### ⚠️ Missing API Functions (referenced but not in api_client.py):\n`;
    r.missingApiFuncs.forEach(c => output += `- \`${c}()\`\n`);
  }
  
  if (r.replitCalls.length > 0) {
    output += `\n### 2. _replit_* internal calls:\n`;
    r.replitCalls.forEach(c => output += `- \`${c}()\`\n`);
  }
  
  if (r.directApiCallCount > 0) {
    output += `\n### 3. Direct _api_call usage: ${r.directApiCallCount} calls\n`;
  }
  
  output += `\n### 4. Direct gspread calls (DEPRECATED):\n`;
  if (r.gspreadCalls.length === 0) {
    output += `None found ✅\n`;
  } else {
    r.gspreadCalls.forEach(g => {
      output += `- **Line ${g.line}:** \`${g.text}\`\n`;
    });
  }
  
  output += `\n### 5. BTN_* Constants Referenced:\n`;
  if (r.btnRefs.length === 0) {
    output += `None found.\n`;
  } else {
    r.btnRefs.forEach(b => {
      const val = btnMap.get(b);
      output += `- \`${b}\`${val ? ' => "' + val + '"' : ' (value not found in app.py)'}\n`;
    });
  }

  if (r.dbRefs.length > 0) {
    output += `\n### 6. Database/MongoDB references:\n`;
    r.dbRefs.forEach(d => output += `- \`${d}\`\n`);
  }
});

// Summary
output += `\n---\n## Summary\n\n`;
output += `| Handler | api* calls | Missing funcs | gspread refs | BTN refs |\n`;
output += `|---------|-----------|--------------|-------------|---------|\n`;
results.forEach(r => {
  output += `| ${r.display} | ${r.apiCalls.length} | ${r.missingApiFuncs.length} | ${r.gspreadCalls.length} | ${r.btnRefs.length} |\n`;
});

output += `\n---\n\n*Audit complete.*\n`;

fs.writeFileSync('/home/node/.openclaw/workspace/audit_report.md', output);
console.log('Report written to audit_report.md');
console.log(`Total api_* functions in api_client.py: ${apiClientFuncs.size}`);
console.log(`Total handlers analyzed: ${results.length}`);
