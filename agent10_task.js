const { Client } = require('ssh2');
const conn = new Client();
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

conn.on('ready', () => {
  console.log('✅ SSH connected');

  // Step 1: Find _CACHE references
  console.log('\n=== Step 1: Find _CACHE references ===');
  conn.exec("grep -n '_CACHE\\|_cache\\|asyncio\\|threading' /root/psvibe-sale-bot/bot/__init__.py 2>&1", (err, stream) => {
    let buf = '';
    stream.on('data', d => buf += d.toString());
    stream.stderr.on('data', d => buf += d.toString());
    stream.on('close', () => {
      console.log(buf || '(no matches or empty)');

      // Step 2: Read current file to understand structure
      console.log('\n=== Step 2: Read __init__.py header ===');
      conn.exec('head -40 /root/psvibe-sale-bot/bot/__init__.py', (err2, stream2) => {
        let buf2 = '';
        stream2.on('data', d => buf2 += d.toString());
        stream2.stderr.on('data', d => buf2 += d.toString());
        stream2.on('close', () => {
          console.log(buf2);

          // Now read the full file content
          conn.exec('cat /root/psvibe-sale-bot/bot/__init__.py', (err3, stream3) => {
            let fullContent = '';
            stream3.on('data', d => fullContent += d.toString());
            stream3.on('close', () => {
              const lines = fullContent.split('\n');
              console.log(`\nTotal lines: ${lines.length}`);

              // Find all lines referencing _CACHE
              console.log('\n=== All _CACHE references ===');
              lines.forEach((line, idx) => {
                if (line.includes('_CACHE') || line.includes('asyncio') || line.includes('threading')) {
                  console.log(`  Line ${idx + 1}: ${line.trim()}`);
                }
              });

              // Step 3: Make changes
              console.log('\n=== Step 3: Apply changes ===');

              let modified = [...lines];

              // Check if asyncio is already imported
              const hasAsyncio = fullContent.includes('import asyncio');
              const hasCacheLock = fullContent.includes('_CACHE_LOCK');

              if (!hasAsyncio) {
                // Find last import line and add after it, or add near top
                let lastImportIdx = -1;
                for (let i = 0; i < Math.min(50, modified.length); i++) {
                  if (/^(import |from )/.test(modified[i].trim())) {
                    lastImportIdx = i;
                  }
                }
                if (lastImportIdx >= 0) {
                  modified.splice(lastImportIdx + 1, 0, 'import asyncio');
                  // Adjust the _CACHE_LOCK insertion point
                } else {
                  modified.unshift('import asyncio');
                }
                console.log('Added: import asyncio');
              } else {
                console.log('asyncio already imported');
              }

              if (!hasCacheLock) {
                // Find _CACHE definition and add _CACHE_LOCK right after
                let cacheIdx = -1;
                for (let i = 0; i < modified.length; i++) {
                  if (modified[i].trim().startsWith('_CACHE') && modified[i].includes('=')) {
                    cacheIdx = i;
                    break;
                  }
                }
                if (cacheIdx >= 0) {
                  modified.splice(cacheIdx + 1, 0, '_CACHE_LOCK = asyncio.Lock()');
                  console.log(`Added: _CACHE_LOCK = asyncio.Lock() (after line ${cacheIdx + 1})`);
                } else {
                  // Fallback: add near imports after _CACHE line
                  for (let i = 0; i < modified.length; i++) {
                    if (modified[i].includes('_CACHE')) {
                      modified.splice(i + 1, 0, '_CACHE_LOCK = asyncio.Lock()');
                      console.log(`Added: _CACHE_LOCK = asyncio.Lock() (after line ${i + 1})`);
                      break;
                    }
                  }
                }
              } else {
                console.log('_CACHE_LOCK already exists');
              }

              // Now wrap cache writes and reads with async locks
              // Find cache write patterns: _CACHE[.*] = or _CACHE[.*].update etc
              // Find cache read patterns: _CACHE.get(, _CACHE[ without assignment on left
              let changes = [];
              let lockedWrites = 0;
              let lockedReads = 0;

              // Re-scan the modified lines for CACHE operations that need locking
              for (let i = 0; i < modified.length; i++) {
                const line = modified[i].trim();
                const indent = modified[i].match(/^(\s*)/)[0];

                // Skip if already wrapped
                if (line.startsWith('async with _CACHE_LOCK:')) continue;
                if (line.startsWith('async with CacheLock:')) continue;

                // Write ops: _CACHE[...] = ..., _CACHE["..."] = ..., _CACHE[...].update/pop/etc
                if (/^\s*_CACHE\[.*\]\s*=\s*/.test(modified[i]) ||
                    /^\s*_CACHE\[.*\]\.(update|pop|clear)\s*\(/.test(modified[i])) {
                  console.log(`  Locking write at original line ~${i + 1}: ${line}`);
                  // Replace the line by wrapping it
                  const oldLine = modified[i];
                  modified[i] = `${indent}async with _CACHE_LOCK:\n${indent}    ${oldLine.trimStart()}`;
                  lockedWrites++;
                }
                // Read ops (standalone, not in assignment context): _CACHE.get(, _CACHE[ not followed by =
                else if (/^\s*.*\b_CACHE\.get\s*\(/.test(modified[i]) ||
                         (/^\s*.*\b_CACHE\[/.test(modified[i]) && !modified[i].includes('=') && !modified[i].includes('async with'))) {
                  // Make sure it's not already inside an async with block
                  console.log(`  Locking read at original line ~${i + 1}: ${line}`);
                  const oldLine = modified[i];
                  modified[i] = `${indent}async with _CACHE_LOCK:\n${indent}    ${oldLine.trimStart()}`;
                  lockedReads++;
                }
              }

              console.log(`\nWrites locked: ${lockedWrites}, Reads locked: ${lockedReads}`);

              // Write the modified file
              const newContent = modified.join('\n');
              
              // Write to a temp file on remote
              const writeCmd = `cat > /tmp/__init__.py.new << 'EOF_AGENT10'
${newContent}
EOF_AGENT10
echo "WRITTEN"`;
              
              conn.exec(writeCmd, (err4, stream4) => {
                let buf4 = '';
                stream4.on('data', d => buf4 += d.toString());
                stream4.stderr.on('data', d => buf4 += d.toString());
                stream4.on('close', () => {
                  console.log(`Remote write: ${buf4.trim()}`);

                  // Move file into place with backup
                  conn.exec('cp /root/psvibe-sale-bot/bot/__init__.py /root/psvibe-sale-bot/bot/__init__.py.bak.agent10 && mv /tmp/__init__.py.new /root/psvibe-sale-bot/bot/__init__.py && echo "FILE_REPLACED"', (err5, stream5) => {
                    let buf5 = '';
                    stream5.on('data', d => buf5 += d.toString());
                    stream5.stderr.on('data', d => buf5 += d.toString());
                    stream5.on('close', () => {
                      console.log(`Replace result: ${buf5.trim()}`);

                      // Step 4: Verify syntax
                      console.log('\n=== Step 4: Verify syntax ===');
                      conn.exec("cd /root/psvibe-sale-bot && python3 -c \"compile(open('bot/__init__.py').read(), '__init__.py', 'exec')\" 2>&1 && echo 'SYNTAX_OK' || echo 'SYNTAX_ERROR'", (err6, stream6) => {
                        let buf6 = '';
                        stream6.on('data', d => buf6 += d.toString());
                        stream6.stderr.on('data', d => buf6 += d.toString());
                        stream6.on('close', () => {
                          console.log(`Syntax check: ${buf6.trim()}`);

                          // Step 5: Final verification - show the changes
                          console.log('\n=== Step 5: Verify _CACHE_LOCK references ===');
                          conn.exec("grep -n '_CACHE_LOCK\\|async with _CACHE_LOCK' /root/psvibe-sale-bot/bot/__init__.py 2>&1", (err7, stream7) => {
                            let buf7 = '';
                            stream7.on('data', d => buf7 += d.toString());
                            stream7.stderr.on('data', d => buf7 += d.toString());
                            stream7.on('close', () => {
                              console.log(buf7);
                              conn.end();
                            });
                          });
                        });
                      });
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH error:', err);
  process.exit(1);
});

conn.connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: fs.readFileSync(KEY_PATH),
  readyTimeout: 10000
});
