const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  console.log('SSH connected');

  // Step 1: Count bare excepts
  const countCmd = `grep -n "except\\s*:" /root/psvibe-sale-bot/bot/__init__.py /root/psvibe-sale-bot/bot/app.py 2>/dev/null; echo "---COUNT---"; grep -c "except\\s*:" /root/psvibe-sale-bot/bot/__init__.py /root/psvibe-sale-bot/bot/app.py 2>/dev/null`;

  conn.exec(countCmd, (err, stream) => {
    if (err) throw err;
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { console.error('STDERR:', data.toString()); });
    stream.on('close', () => {
      console.log('=== GREP RESULTS ===');
      console.log(output);

      // Now read the files
      readAndFixFiles();
    });
  });
});

function readAndFixFiles() {
  const files = [
    '/root/psvibe-sale-bot/bot/__init__.py',
    '/root/psvibe-sale-bot/bot/app.py'
  ];

  let remaining = files.length;
  const fileContents = {};

  files.forEach((filePath) => {
    conn.exec(`cat "${filePath}" 2>/dev/null || echo "FILE_NOT_FOUND"`, (err, stream) => {
      if (err) throw err;
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.on('close', () => {
        if (output.includes('FILE_NOT_FOUND')) {
          console.log(`File not found: ${filePath}`);
        } else {
          fileContents[filePath] = output;
        }
        remaining--;
        if (remaining === 0) {
          analyzeAndFix(fileContents);
        }
      });
    });
  });
}

function analyzeAndFix(fileContents) {
  const results = {};

  for (const [filePath, content] of Object.entries(fileContents)) {
    const lines = content.split('\n');
    const bareExceptLines = [];

    lines.forEach((line, idx) => {
      const trimmed = line.trim();
      // Match bare except: or except Exception: or except Exception, e:
      if (/^except\s*:/.test(trimmed)) {
        bareExceptLines.push({ lineNum: idx + 1, text: line, type: 'bare' });
      }
    });

    results[filePath] = { lines, bareExceptLines };
  }

  // Print findings
  for (const [filePath, data] of Object.entries(results)) {
    console.log(`\n=== ${filePath} ===`);
    console.log(`Total bare excepts: ${data.bareExceptLines.length}`);
    data.bareExceptLines.forEach((e) => {
      console.log(`  Line ${e.lineNum}: ${e.text.trim()}`);
    });
  }

  // Determine functions for context
  // Now fix them
  const fixCommands = [];

  for (const [filePath, data] of Object.entries(results)) {
    if (data.bareExceptLines.length === 0) continue;

    let newContent = data.lines.join('\n');
    const needsLoggerImport = !newContent.includes('logger = logging.getLogger')

    // Process fixes from bottom to top to preserve line numbers
    const sorted = [...data.bareExceptLines].sort((a, b) => b.lineNum - a.lineNum);

    for (const exceptInfo of sorted) {
      const idx = exceptInfo.lineNum - 1;
      const line = data.lines[idx];
      const indent = line.match(/^(\s*)/)[1];
      const innerIndent = indent + '    ';

      // Find the function name context
      let funcName = 'unknown';
      for (let j = idx - 1; j >= 0; j--) {
        const fl = data.lines[j].trim();
        const match = fl.match(/^(async\s+)?def\s+(\w+)/);
        if (match) {
          funcName = match[2];
          break;
        }
      }

      // Replace bare except: with except Exception as e:
      if (/^except\s*:\s*$/.test(line.trim())) {
        newContent = newContent.replace(line, `${indent}except Exception as e:`);
      }

      // Add logging line after the except line (in the new content)
      // We'll handle this more carefully in the script below
    }

    // We need a more robust approach - let's do per-file fixes
    console.log(`\nGenerating fix for ${filePath}...`);
    fixCommands.push({ filePath, data });
  }

  // Apply fixes
  if (fixCommands.length === 0) {
    console.log('\nNo bare excepts to fix!');
    conn.end();
    return;
  }

  applyFixes(fixCommands);
}

function applyFixes(fixCommands) {
  let remaining = fixCommands.length;

  fixCommands.forEach(({ filePath, data }) => {
    let newContent = data.lines.join('\n');
    const needsLoggerImport = !newContent.includes('logger = logging.getLogger');

    // Fix from bottom to top
    const sorted = [...data.bareExceptLines].sort((a, b) => b.lineNum - a.lineNum);

    for (const exceptInfo of sorted) {
      const idx = exceptInfo.lineNum - 1;
      const line = data.lines[idx];
      const indent = line.match(/^(\s*)/)[1];
      const innerIndent = indent + '    ';

      // Find function name
      let funcName = 'unknown';
      for (let j = idx - 1; j >= 0; j--) {
        const match = data.lines[j].trim().match(/^(async\s+)?def\s+(\w+)/);
        if (match) {
          funcName = match[2];
          break;
        }
      }

      const originalLine = line;

      // Check if it's a bare except: (no Exception)
      if (/^except\s*:\s*$/.test(line.trim())) {
        newContent = newContent.replace(originalLine, `${indent}except Exception as e:\n${innerIndent}logger.error(f"Error in ${funcName}: {e}", exc_info=True)`);
      }
    }

    // Add logging import if needed
    if (needsLoggerImport) {
      // Check if logging is already imported
      if (!newContent.includes('import logging')) {
        // Add after the last import line or at the top
        const lines2 = newContent.split('\n');
        let lastImportIdx = -1;
        for (let i = 0; i < lines2.length; i++) {
          if (/^(import|from)\s+/.test(lines2[i].trim())) {
            lastImportIdx = i;
          }
        }
        if (lastImportIdx >= 0) {
          lines2.splice(lastImportIdx + 1, 0, 'import logging');
          lines2.splice(lastImportIdx + 2, 0, 'logger = logging.getLogger(__name__)');
        } else {
          lines2.unshift('logger = logging.getLogger(__name__)');
          lines2.unshift('import logging');
        }
        newContent = lines2.join('\n');
      } else if (!newContent.includes('logger = logging.getLogger')) {
        // logging imported but no logger
        const lines2 = newContent.split('\n');
        let importIdx = -1;
        for (let i = 0; i < lines2.length; i++) {
          if (lines2[i].trim() === 'import logging') {
            importIdx = i;
            break;
          }
        }
        if (importIdx >= 0) {
          lines2.splice(importIdx + 1, 0, 'logger = logging.getLogger(__name__)');
        }
        newContent = lines2.join('\n');
      }
    }

    // Write the fixed file
    const base64Content = Buffer.from(newContent).toString('base64');
    const writeCmd = `echo "${base64Content}" | base64 -d > "${filePath}"`;

    conn.exec(writeCmd, (err, stream) => {
      if (err) throw err;
      let out = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.stderr.on('data', (d) => { console.error('WERR:', d.toString()); });
      stream.on('close', () => {
        console.log(`Wrote fixed file: ${filePath} (exit: ${stream.exitCode})`);
        remaining--;
        if (remaining === 0) {
          verifySyntax();
        }
      });
    });
  });
}

function verifySyntax() {
  console.log('\n=== Verifying syntax ===');

  const files = [
    '/root/psvibe-sale-bot/bot/__init__.py',
    '/root/psvibe-sale-bot/bot/app.py'
  ];

  let remaining = files.length;

  files.forEach((filePath) => {
    const cmd = `python3 -c "compile(open('${filePath}').read(), '${path.basename(filePath)}', 'exec')" 2>&1 && echo "SYNTAX_OK" || echo "SYNTAX_ERROR"`;

    conn.exec(cmd, (err, stream) => {
      if (err) throw err;
      let out = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.on('close', () => {
        console.log(`${filePath}: ${out.trim()}`);

        // Also verify fixes applied by re-grepping
        const grepCmd = `grep -n "except\\s*:" /root/psvibe-sale-bot/bot/__init__.py /root/psvibe-sale-bot/bot/app.py 2>/dev/null; echo "Done"`;
        remaining--;
        if (remaining === 0) {
          conn.exec(grepCmd, (err2, stream2) => {
            if (err2) throw err2;
            let gout = '';
            stream2.on('data', (d) => { gout += d.toString(); });
            stream2.on('close', () => {
              console.log('\n=== Post-fix grep ===');
              console.log(gout);
              conn.end();
            });
          });
        }
      });
    });
  });
}

conn.on('error', (err) => {
  console.error('SSH error:', err);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
