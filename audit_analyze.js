const fs = require('fs');

const files = {
  main: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_main.py', 'utf8'),
  init: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot___init__.py', 'utf8'),
  app: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot_app.py', 'utf8'),
  handlers: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot_handlers.py', 'utf8'),
};

// V2 combined
const v2Combined = files.init + '\n' + files.app + '\n' + files.handlers;

// Extract function/class definitions
function extractDefs(code) {
  const defs = {
    functions: [],
    classes: [],
    decorators: [],
    imports: [],
    top_level_code: [],
  };
  
  const lines = code.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    
    // Function definitions
    const funcMatch = trimmed.match(/^(async\s+)?def\s+(\w+)\s*\(/);
    if (funcMatch) {
      defs.functions.push({ name: funcMatch[2], line: i + 1, isAsync: !!funcMatch[1] });
    }
    
    // Class definitions
    const classMatch = trimmed.match(/^class\s+(\w+)/);
    if (classMatch) {
      defs.classes.push({ name: classMatch[1], line: i + 1 });
    }
    
    // Decorators
    if (trimmed.startsWith('@')) {
      defs.decorators.push({ decorator: trimmed.split('(')[0], line: i + 1 });
    }
    
    // Imports
    if (trimmed.match(/^(from\s+\S+\s+import|import\s+)/)) {
      defs.imports.push({ line: i + 1, statement: trimmed });
    }
  }
  
  return defs;
}

// Extract handler decorators specifically
function extractHandlers(code) {
  const lines = code.split('\n');
  const handlers = [];
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    const dhMatch = trimmed.match(/@(?:dp\.)?(message_handler|callback_query_handler|inline_handler|channel_post_handler|poll_handler|edited_message_handler)\(/);
    const appMatch = trimmed.match(/@(?:app\.|application\.|bot\.)?(message|callback_query|inline_query|channel_post|poll)\(/);
    if (dhMatch || appMatch) {
      handlers.push({
        type: (dhMatch && dhMatch[1]) || (appMatch && appMatch[1]),
        line: i + 1,
        raw: trimmed,
      });
    }
  }
  return handlers;
}

// Extract Google Sheets references
function extractGoogleSheetsRefs(code) {
  const refs = [];
  const lines = code.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (trimmed.match(/gspread|gsheet|spreadsheet|worksheet|sheet\.|\.worksheet|open_by|oauth|service_account/)) {
      refs.push({ line: i + 1, content: trimmed.substring(0, 200) });
    }
  }
  return refs;
}

// Extract error handling patterns
function extractErrorHandling(code) {
  const patterns = [];
  const lines = code.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (trimmed.match(/^try\s*:/)) {
      patterns.push({ line: i + 1, type: 'try' });
    }
    if (trimmed.match(/^except\b/)) {
      patterns.push({ line: i + 1, type: 'except', content: trimmed });
    }
    if (trimmed.match(/^raise\b/)) {
      patterns.push({ line: i + 1, type: 'raise', content: trimmed });
    }
    if (trimmed.match(/logger\.(error|exception|warning|info)/) || trimmed.match(/logging\.(error|exception|warning|info)/)) {
      patterns.push({ line: i + 1, type: 'log', content: trimmed.substring(0, 200) });
    }
  }
  return patterns;
}

console.log('=== V1 (main.py) Definitions ===');
const v1Defs = extractDefs(files.main);
console.log(`Functions: ${v1Defs.functions.length}`);
console.log(`Classes: ${v1Defs.classes.length}`);
console.log(`Imports: ${v1Defs.imports.length}`);
console.log(`Decorators: ${v1Defs.decorators.length}`);
console.log('\nFunction names:');
v1Defs.functions.forEach(f => console.log(`  ${f.isAsync ? 'async ' : ''}def ${f.name}() at line ${f.line}`));

console.log('\n=== V2 (combined) Definitions ===');
const v2Defs = extractDefs(v2Combined);
console.log(`Functions: ${v2Defs.functions.length}`);
console.log(`Classes: ${v2Defs.classes.length}`);
console.log(`Imports: ${v2Defs.imports.length}`);
console.log(`Decorators: ${v2Defs.decorators.length}`);
console.log('\nFunction names (__init__.py):');
const initDefs = extractDefs(files.init);
initDefs.functions.forEach(f => console.log(`  ${f.isAsync ? 'async ' : ''}def ${f.name}() at line ${f.line}`));

console.log('\nFunction names (app.py):');
const appDefs = extractDefs(files.app);
appDefs.functions.forEach(f => console.log(`  ${f.isAsync ? 'async ' : ''}def ${f.name}() at line ${f.line}`));

console.log('\nFunction names (handlers.py):');
const handlerDefs = extractDefs(files.handlers);
handlerDefs.functions.forEach(f => console.log(`  ${f.isAsync ? 'async ' : ''}def ${f.name}() at line ${f.line}`));

console.log('\n=== V1 Handler Decorators ===');
const v1Handlers = extractHandlers(files.main);
console.log(`Count: ${v1Handlers.length}`);
v1Handlers.forEach(h => console.log(`  ${h.type} at line ${h.line}`));

console.log('\n=== V2 Handler Decorators ===');
const v2Handlers = extractHandlers(v2Combined);
console.log(`Count: ${v2Handlers.length}`);
v2Handlers.forEach(h => console.log(`  ${h.type} at line ${h.line}`));

// Compare function names
console.log('\n=== FUNCTION COMPARISON ===');
const v1Names = new Set(v1Defs.functions.map(f => f.name));
const v2Names = new Set(v2Defs.functions.map(f => f.name));

const onlyInV1 = [...v1Names].filter(n => !v2Names.has(n));
const onlyInV2 = [...v2Names].filter(n => !v1Names.has(n));
const inBoth = [...v1Names].filter(n => v2Names.has(n));

console.log(`\nIn both: ${inBoth.length}`);
console.log(`Only in V1: ${onlyInV1.length}`);
onlyInV1.forEach(n => console.log(`  - ${n}`));
console.log(`Only in V2: ${onlyInV2.length}`);
onlyInV2.forEach(n => console.log(`  + ${n}`));

// Count error handling
console.log('\n=== ERROR HANDLING COMPARISON ===');
const v1Errors = extractErrorHandling(files.main);
const v2Errors = extractErrorHandling(v2Combined);
console.log(`V1 try/except blocks: ${v1Errors.filter(e => e.type === 'try').length}`);
console.log(`V2 try/except blocks: ${v2Errors.filter(e => e.type === 'try').length}`);
console.log(`V1 log calls: ${v1Errors.filter(e => e.type === 'log').length}`);
console.log(`V2 log calls: ${v2Errors.filter(e => e.type === 'log').length}`);

// Count Google Sheets references
console.log('\n=== GOOGLE SHEETS ACCESS COMPARISON ===');
const v1GS = extractGoogleSheetsRefs(files.main);
const v2GS = extractGoogleSheetsRefs(v2Combined);
console.log(`V1 GS references: ${v1GS.length}`);
console.log(`V2 GS references: ${v2GS.length}`);
