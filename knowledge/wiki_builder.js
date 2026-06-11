#!/usr/bin/env node
/**
 * wiki_builder.js — Knowledge Base Wiki Builder
 * 
 * Generates and maintains the PS VIBE Wiki from existing documentation.
 * 
 * Usage:
 *   node wiki_builder.js build     → Generate wiki pages from sources
 *   node wiki_builder.js index     → Show wiki structure
 *   node wiki_builder.js search    → Search all wiki content
 *   node wiki_builder.js stats     → Wiki statistics
 */

const fs = require('fs');
const path = require('path');

const WIKI_DIR = path.join(__dirname, 'docs');
const BUILD_DIR = path.join(__dirname, 'docs', '_build');
const SOURCES = {
  infrastructure: ['/root/psvibe-sales-bot/DISASTER_RECOVERY.md', '/root/psvibe-sales-bot/PROJECT_STRUCTURE.md', '/root/psvibe_api_server/config.py'],
  services: ['/root/psvibe-sales-bot/STAFF_RUNBOOK.md', '/root/psvibe-sales-bot/API_ENDPOINTS.md', '/root/psvibe-sales-bot/CHANGE_LOG.md'],
  operations: ['/root/psvibe-sales-bot/GRAND_OPENING_CHECKLIST.md', '/root/psvibe-sales-bot/V2_STATE.md'],
  business: ['/root/psvibe-sales-bot/DB_SCHEMA.md'],
};

// ── Load wiki structure ──
function getStructure() {
  const structure = {};
  
  function walk(dir, prefix = '') {
    if (!fs.existsSync(dir)) return;
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (entry.isDirectory() && !entry.name.startsWith('_')) {
        structure[rel] = { type: 'dir', path: path.join(dir, entry.name) };
        walk(path.join(dir, entry.name), rel);
      } else if (entry.name.endsWith('.md') && entry.name !== 'INDEX.md') {
        structure[rel] = { type: 'file', path: path.join(dir, entry.name) };
      }
    }
  }
  
  walk(WIKI_DIR);
  return structure;
}

// ── 1. Build wiki from sources ──
async function buildWiki() {
  console.log('📚 Wiki Builder — Generating pages from sources...\n');
  fs.mkdirSync(BUILD_DIR, { recursive: true });

  // Create section folders
  for (const section of Object.keys(SOURCES)) {
    const sectionDir = path.join(WIKI_DIR, section);
    fs.mkdirSync(sectionDir, { recursive: true });
  }

  let generated = 0;
  const { Client } = require('ssh2');
  const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

  function sshRead(filepath) {
    return new Promise((resolve, reject) => {
      const conn = new Client();
      let out = '';
      conn.on('ready', () => {
        conn.exec(`cat ${filepath} 2>/dev/null || echo "FILE_NOT_FOUND"`, (err, stream) => {
          if (err) { conn.end(); reject(err); return; }
          stream.on('data', d => out += d.toString());
          stream.on('close', () => { conn.end(); resolve(out.trim()); });
        });
      });
      conn.on('error', reject);
      conn.connect({
        host: '5.223.81.16', port: 22, username: 'root',
        privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 10000,
      });
    });
  }

  for (const [section, files] of Object.entries(SOURCES)) {
    for (const filepath of files) {
      const basename = path.basename(filepath).replace(/\.md$/i, '');
      const destPath = path.join(WIKI_DIR, section, `${basename.toLowerCase()}.md`);
      
      try {
        const content = await sshRead(filepath, 10000);
        if (content && content !== 'FILE_NOT_FOUND') {
          const wikiContent = [
            `# ${basename.replace(/_/g, ' ')}`,
            `> Auto-imported from \`${filepath}\``,
            ``,
            content,
            ``,
            `---`,
            `*Imported on ${new Date().toISOString().split('T')[0]}*`,
          ].join('\n');
          
          fs.writeFileSync(destPath, wikiContent);
          generated++;
          process.stdout.write(`  ✅ ${section}/${basename.toLowerCase()}.md\n`);
        } else {
          process.stdout.write(`  ⚠️ ${section}/${basename.toLowerCase()}.md — not found on VPS\n`);
        }
      } catch (err) {
        process.stdout.write(`  ❌ ${section}/${basename.toLowerCase()}.md — ${err.message}\n`);
      }
    }
  }

  console.log(`\n📊 Generated: ${generated} wiki pages`);

  // Rebuild index
  rebuildIndex();
  console.log('📊 Index rebuilt');
}

// ── 2. Rebuild INDEX.md ──
function rebuildIndex() {
  // Index is already manually maintained - just verify it exists
  const indexPath = path.join(WIKI_DIR, 'INDEX.md');
  if (!fs.existsSync(indexPath)) {
    fs.writeFileSync(indexPath, '# PS VIBE Wiki\n\n_Wiki index missing — run `node wiki_builder.js build`_\n');
  }

  // Auto-update with actual file count
  const structure = getStructure();
  const fileCount = Object.values(structure).filter(s => s.type === 'file').length;
  const dirCount = Object.values(structure).filter(s => s.type === 'dir').length;

  return { files: fileCount, dirs: dirCount };
}

// ── 3. Search wiki ──
function searchWiki(query) {
  if (!query) { console.log('Usage: node wiki_builder.js search <query>'); return; }

  const structure = getStructure();
  const q = query.toLowerCase();
  let results = 0;

  console.log(`🔍 Searching wiki for "${query}"...\n`);

  for (const [key, entry] of Object.entries(structure)) {
    if (entry.type !== 'file') continue;
    const content = fs.readFileSync(entry.path, 'utf8');
    const lines = content.split('\n');
    
    let matchedLines = [];
    lines.forEach((line, i) => {
      if (line.toLowerCase().includes(q)) {
        matchedLines.push(`      L${i+1}: ${line.trim().substring(0, 80)}`);
      }
    });

    if (matchedLines.length > 0) {
      results++;
      console.log(`  📄 ${key}`);
      matchedLines.slice(0, 3).forEach(l => console.log(l));
      if (matchedLines.length > 3) console.log(`      ... and ${matchedLines.length - 3} more matches`);
      console.log();
    }
  }

  console.log(`📊 ${results} files matched`);
}

// ── 4. Stats ──
function wikiStats() {
  const structure = getStructure();
  const files = Object.values(structure).filter(s => s.type === 'file');
  const dirs = Object.values(structure).filter(s => s.type === 'dir');

  let totalChars = 0;
  let totalLines = 0;
  files.forEach(f => {
    try {
      const content = fs.readFileSync(f.path, 'utf8');
      totalChars += content.length;
      totalLines += content.split('\n').length;
    } catch {}
  });

  console.log('📚 Wiki Statistics');
  console.log('━━━━━━━━━━━━━━━━━');
  console.log(`📁 Sections:      ${dirs.length}`);
  console.log(`📄 Pages:         ${files.length}`);
  console.log(`📝 Total Lines:   ${totalLines.toLocaleString()}`);
  console.log(`📝 Total Chars:   ${totalChars.toLocaleString()}`);
  console.log(`📏 Avg Page Size: ${Math.round(totalChars / Math.max(files.length, 1))} chars`);

  if (files.length > 0) {
    console.log(`\n📋 Pages:`);
    Object.entries(structure)
      .filter(([_, e]) => e.type === 'file')
      .forEach(([key, entry]) => {
        const size = fs.statSync(entry.path).size;
        const sizeStr = size > 1024 ? `${(size/1024).toFixed(1)} KB` : `${size} B`;
        console.log(`  📄 ${key} (${sizeStr})`);
      });
  }
}

// ── CLI ──
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'stats';

  switch (cmd) {
    case 'build':
      await buildWiki();
      break;

    case 'index':
    case 'rebuild':
      const result = rebuildIndex();
      console.log(`📋 Wiki: ${result.files} pages in ${result.dirs} sections`);
      break;

    case 'search':
      searchWiki(args.slice(1).join(' '));
      break;

    case 'stats':
      wikiStats();
      break;

    default:
      console.log(`
📚 Wiki Builder
  build   → Import docs from VPS sources
  index   → Rebuild navigation index
  search  → Search wiki content
  stats   → Wiki statistics
`);
  }
}

main().catch(err => console.error(`❌ ${err.message}`));
