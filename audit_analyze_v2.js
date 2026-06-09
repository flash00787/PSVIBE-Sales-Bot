const fs = require('fs');
const path = require('path');

const auditDir = '/home/node/.openclaw/workspace/audit_split';

// ============================================================
// LOAD SOURCE FILES
// ============================================================

// 1. api_client.py — all api_* functions
const apiClientRaw = fs.readFileSync(path.join(auditDir, 'api_client.py'), 'utf8');
const apiClientFuncs = new Set();
let m;
const apiClientRegex = /^def (api_\w+)/gm;
while ((m = apiClientRegex.exec(apiClientRaw)) !== null) apiClientFuncs.add(m[1]);

// Endpoints as called via _api_call
const apiClientEndpoints = new Map();
const epRegex = /_api_call\("(\w+)",\s*"([^"]+)"/g;
while ((m = epRegex.exec(apiClientRaw)) !== null) {
  apiClientEndpoints.set(m[2], m[1]);
}

// 2. API Server app.py — actual FastAPI routes
const apiServerRaw = fs.readFileSync(path.join(auditDir, 'api_server_app.py'), 'utf8');
const apiServerRoutes = new Map();
// Look for @router.get, @router.post, @router.put, @router.delete
const serverRouteRegex = /@\w+\.(?:get|post|put|delete)\s*\(\s*["']([^"']+)["']/g;
while ((m = serverRouteRegex.exec(apiServerRaw)) !== null) {
  apiServerRoutes.set(m[1].replace(/^\//,''), m[0]);
}
// Also @app.get, @app.post etc
const appRouteRegex = /@app\.(?:get|post|put|delete)\s*\(\s*["']([^"']+)["']/g;
while ((m = appRouteRegex.exec(apiServerRaw)) !== null) {
  apiServerRoutes.set(m[1].replace(/^\//,''), m[0]);
}
// Also check /api/ prefix routes
const apiPrefixRegex = /["']\/api\/([^"']+)["']/g;
while ((m = apiPrefixRegex.exec(apiServerRaw)) !== null) {
  apiServerRoutes.set(m[1], 'REF /api/'+m[1]);
}

// 3. Bot __init__.py — BTN_* constants
const botInitRaw = fs.readFileSync(path.join(auditDir, 'bot_init.py'), 'utf8');
const btnDefs = new Map();
botInitRaw.split('\n').forEach(line => {
  const bm = line.match(/^(BTN_\w+)\s*=\s*["'].+?["']/);
  if (bm) btnDefs.set(bm[1], line.trim());
});

// 4. Also find _replit_get / _replit_post / _api_call references in bot __init__.py
const replitFuncs = new Set();
const initFuncRegex = /^def (_replit_\w+|_api_call)\b/gm;
while ((m = initFuncRegex.exec(botInitRaw)) !== null) replitFuncs.add(m[1]);

// ============================================================
// HANDLER FILES TO AUDIT
// ============================================================
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

const results = [];

handlerFiles.forEach(f => {
  const content = fs.readFileSync(path.join(auditDir, f), 'utf8');
  const lines = content.split('\n');
  const fname = f.replace('handlers_', '').replace('.py', '');
  
  const entry = {
    file: f,
    display: `handlers/${fname}.py`,
    lineCount: lines.length,
    apiCalls: new Map(),    // api_func -> { lineNumbers }
    replitCalls: new Map(), // _replit_* -> { lineNumbers }
    btnRefs: new Set(),
    gspreadRefs: [],        // { line, text }
    directApiCallLines: [], // lines using _api_call directly
    worksheetOps: [],       // direct sheet operations
  };
  
  // Scan each line
  lines.forEach((line, i) => {
    const lineno = i + 1;
    const trimmed = line.trim();
    
    // api_*() calls
    const apiMatch = trimmed.match(/(api_\w+)\s*\(/);
    if (apiMatch) {
      if (!entry.apiCalls.has(apiMatch[1])) entry.apiCalls.set(apiMatch[1], []);
      entry.apiCalls.get(apiMatch[1]).push(lineno);
    }
    
    // _replit_*() calls
    const rpMatch = trimmed.match(/(_replit_\w+)\s*\(/);
    if (rpMatch) {
      if (!entry.replitCalls.has(rpMatch[1])) entry.replitCalls.set(rpMatch[1], []);
      entry.replitCalls.get(rpMatch[1]).push(lineno);
    }
    
    // _api_call direct
    if (trimmed.match(/_api_call\s*\(/)) {
      entry.directApiCallLines.push(lineno);
    }
    
    // BTN_* references
    const btnMatches = trimmed.match(/\b(BTN_\w+)\b/g);
    if (btnMatches) btnMatches.forEach(b => entry.btnRefs.add(b));
    
    // Gspread / sheet operations
    if (trimmed.match(/(gc\.|gspread|\.worksheet|\.values_get|\.values_update|sheet\.append|sheet\.update|sheet\.get_all|sh\.worksheet|\.acell|\.range|\.batch_update|\.update_cell|\.append_row|\.delete_row|Spreadsheet)/i)) {
      entry.gspreadRefs.push({ line: lineno, text: trimmed.substring(0, 120) });
    }
    
    // MongoDB/database references
    if (trimmed.match(/\b(mongo|mongodb|collection\.|db\.|insert_one|find_one|update_one|delete_one|\.find\(|\.aggregate)/i)) {
      if (!entry.worksheetOps) entry.worksheetOps = [];
      entry.worksheetOps.push({ line: lineno, type: 'db', text: trimmed.substring(0, 120) });
    }
  });
  
  results.push(entry);
});

// ============================================================
// BUILD REPORT
// ============================================================
let out = `# Audit Report: Booking/Stock/Other Handlers
**Generated:** ${new Date().toISOString()}
**Source:** \`/root/psvibe-sales-bot/bot/\`

---

## 1. api_client.py — Available API Functions (${apiClientFuncs.size} total)

\`\`\`
${[...apiClientFuncs].sort().join('\n')}
\`\`\`

---

## 2. API Server Routes (FastAPI in /root/psvibe_api_server/app.py)

\`\`\`
${[...apiServerRoutes.entries()].sort((a,b) => a[0].localeCompare(b[0])).map(([k,v]) => `${k}`).join('\n')}
\`\`\`

---

## 3. Replit Internal Functions (from bot __init__.py)

\`\`\`
${[...replitFuncs].sort().join('\n')}
\`\`\`

---

## 4. BTN_* Constants (from bot __init__.py)

\`\`\`
${[...btnDefs.entries()].sort().map(([k,v]) => v).join('\n')}
\`\`\`

---

## 5. Handler-by-Handler Analysis

`;

results.forEach(r => {
  out += `\n### 📁 ${r.display} (${r.lineCount} lines)\n\n`;
  
  // api_* calls
  out += `**5.1 — api_* calls made (${r.apiCalls.size} unique):**\n\n`;
  if (r.apiCalls.size === 0) {
    out += `None found.\n\n`;
  } else {
    for (const [func, lines] of [...r.apiCalls.entries()].sort()) {
      const exists = apiClientFuncs.has(func) ? '✅' : '❌';
      const lineStr = lines.join(', ');
      out += `- ${exists} \`${func}()\` — lines: ${lineStr}\n`;
    }
    out += '\n';
  }
  
  // _replit_* calls
  if (r.replitCalls.size > 0) {
    out += `**5.2 — _replit_* calls (bypasses api_client.py):**\n\n`;
    for (const [func, lines] of [...r.replitCalls.entries()].sort()) {
      const lineStr = lines.join(', ');
      out += `- \`${func}()\` — lines: ${lineStr}\n`;
    }
    out += '\n';
  }
  
  // Direct _api_call
  if (r.directApiCallLines.length > 0) {
    out += `**5.3 — Direct _api_call usage (bypassing typed wrappers):**\n`;
    out += `- Lines: ${r.directApiCallLines.join(', ')}\n\n`;
  }
  
  // Gspread refs
  out += `**5.4 — Direct gspread/sheet calls (DEPRECATED):**\n\n`;
  if (r.gspreadRefs.length === 0) {
    out += `None found ✅\n\n`;
  } else {
    r.gspreadRefs.forEach(g => {
      out += `- ❌ **Line ${g.line}:** \`${g.text}\`\n`;
    });
    out += '\n';
  }
  
  // BTN_* refs
  out += `**5.5 — BTN_* Constants Referenced (${r.btnRefs.size} unique):**\n\n`;
  if (r.btnRefs.size === 0) {
    out += `None found.\n\n`;
  } else {
    const sorted = [...r.btnRefs].sort();
    sorted.forEach(b => {
      const def = btnDefs.get(b);
      out += `- \`${b}\`${def ? '' : ' ❓ (not defined in bot __init__)'}\n`;
    });
    out += '\n';
  }

  // Cross-reference api_client endpoints vs API server
  out += `**5.6 — Endpoint Cross-Reference (API Client vs Server):**\n\n`;
  // For each api_* call, check what path it maps to
  const callsToPaths = new Map();
  for (const [func, lines] of r.apiCalls) {
    // Find the path this function calls in api_client.py
    // Search api_client.py for this function definition
    const funcDefMatch = apiClientRaw.match(new RegExp(`def ${func}\\(`, 'm'));
    if (funcDefMatch) {
      // Find the preceding lines to extract the path
      const preLines = apiClientRaw.substring(0, funcDefMatch.index).split('\n');
      // Find the _api_call line within this function (use post-match)
      const postMatch = apiClientRaw.substring(funcDefMatch.index).match(/_api_call\("([^"]+)",\s*"([^"]+)"[^)]*\)/);
      if (postMatch) {
        const method = postMatch[1];
        let path = postMatch[2];
        callsToPaths.set(func, { method, path });
      }
    }
  }
  
  if (callsToPaths.size > 0) {
    for (const [func, {method, path}] of [...callsToPaths.entries()].sort()) {
      // Check if route exists in server
      const routeKey = path.replace(/^\/+/,'').replace(/\/\{[^}]+\}/g, '/{id}');
      const routeKey2 = path.replace(/^\/+/,'');
      const existsInServer = apiServerRoutes.has(routeKey) || apiServerRoutes.has(routeKey2);
      // Check for pattern match
      let patMatch = false;
      for (const serverRoute of apiServerRoutes.keys()) {
        const serverPattern = serverRoute.replace(/\{[^}]+\}/g, '{param}');
        const clientPattern = routeKey2.replace(/\/\{?[^}\/]+\}?/g, '/{param}');
        if (serverPattern === clientPattern) { patMatch = true; break; }
        // Also try simply: does the client path match any server route with 1 segment diff?
        if (serverRoute.includes(routeKey2.split('/')[0])) patMatch = true;
      }
      const serverOk = existsInServer || patMatch;
      const serverMethod = apiServerRoutes.get(routeKey) || apiServerRoutes.get(routeKey2);
      out += `- \`${func}()\` → ${method} \`/api/${path}\` — ${serverOk ? '✅ Found in server' : '❌ Not found in server'}${serverMethod ? ` (matched: \`${serverMethod.substring(0,80)}\`)` : ''}\n`;
    }
  }
  out += '\n';
});

// ============================================================
// SUMMARY TABLE
// ============================================================
out += `---\n\n## Summary Table\n\n`;
out += `| Handler | Lines | api* calls | Missing API funcs | Gspread refs | BTN refs | Direct _api_call |\n`;
out += `|---------|------:|-----------:|------------------:|-------------:|---------:|-----------------:|\n`;
results.forEach(r => {
  const missing = [...r.apiCalls.keys()].filter(f => !apiClientFuncs.has(f));
  out += `| ${r.display} | ${r.lineCount} | ${r.apiCalls.size} | ${missing.length} | ${r.gspreadRefs.length} | ${r.btnRefs.size} | ${r.directApiCallLines.length} |\n`;
});

out += `\n---\n\n*Audit complete.*\n`;

fs.writeFileSync('/home/node/.openclaw/workspace/audit_report_final.md', out);
console.log('Report written to audit_report_final.md');
console.log(`api_* functions in api_client.py: ${apiClientFuncs.size}`);
console.log(`API Server routes: ${apiServerRoutes.size}`);
console.log(`BTN constants: ${btnDefs.size}`);
console.log(`Replit functions: ${replitFuncs.size}`);

// Also log which api_* functions are NOT in api_client.py
let allMissing = new Set();
results.forEach(r => {
  for (const f of r.apiCalls.keys()) {
    if (!apiClientFuncs.has(f)) allMissing.add(f);
  }
});
if (allMissing.size > 0) {
  console.log(`\n⚠️ Missing API functions across ALL handlers:`);
  allMissing.forEach(f => console.log(`  - ${f}()`));
}
