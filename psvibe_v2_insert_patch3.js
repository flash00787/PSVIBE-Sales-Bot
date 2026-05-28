#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

function sshRun(cmd, label) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); return reject(err); }
        let out = '', errOut = '';
        stream.on('data', d => out += d);
        stream.stderr.on('data', d => errOut += d);
        stream.on('close', (code) => {
          conn.end();
          console.log(`\n=== ${label} (exit ${code}) ===`);
          if (out.trim()) console.log(out.trim());
          if (errOut.trim()) console.log('STDERR:', errOut.trim());
          resolve({ code, out, errOut });
        });
      });
    }).connect({
      host: '167.71.196.120',
      username: 'root',
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
    });
  });
}

async function main() {
  // Use sed directly to insert _replit_patch after line 1451 (end of _replit_delete, before _load_cfg)
  // Read the patch code, escape it, and insert
  const patchLines = [
    '',
    'def _replit_patch(path: str, body: dict):',
    '    """PATCH JSON to API server. Returns parsed response or None on error.',
    '    On HTTP 409 conflict, returns dict with \'error\' key instead of None."""',
    '    base = _api_base()',
    '    if not base:',
    '        return None',
    '    try:',
    '        import urllib.request as _req',
    '        import urllib.error as _err',
    '        data = json.dumps(body).encode()',
    '        req  = _req.Request(',
    '            f"{base}/api/{path}",',
    '            data=data,',
    '            headers={"Content-Type": "application/json", "X-API-Key": _API_KEY},',
    '            method="PATCH",',
    '        )',
    '        with _req.urlopen(req, timeout=10) as resp:',
    '            return json.loads(resp.read().decode())',
    '    except _err.HTTPError as e:',
    '        try:',
    '            err_body = json.loads(e.read().decode())',
    '        except Exception:',
    '            err_body = {"error": f"http_{e.code}"}',
    '        err_body["__status__"] = e.code',
    '        logging.warning("API PATCH /%s HTTP %s: %s", path, e.code, err_body)',
    '        return err_body',
    '    except Exception as e:',
    '        logging.warning("API PATCH /%s failed: %s", path, e)',
    '        return None',
    ''
  ];

  // Write patch to temp file
  const patchContent = patchLines.join('\n');
  
  // Write the patch to a file on VPS
  const cmd = `cat > /tmp/patch.txt << 'PATCHEOF'
${patchContent}
PATCHEOF
echo "Patch file written"`;
  
  await sshRun(cmd, 'Write patch file');
  
  // Verify patch file
  await sshRun('head -5 /tmp/patch.txt', 'Verify patch file');

  // Insert after line 1451 for both files using sed
  for (const fpath of ['/root/Sales-Tele-Bot_refactored/bot/__init__.py', '/root/staging/bot_src/bot/__init__.py']) {
    // Use sed to insert after line 1451
    await sshRun(`sed -i '1451 r /tmp/patch.txt' ${fpath} && echo "INSERTED in ${fpath}"`, `Insert patch into ${fpath}`);
  }

  // Verify syntax
  await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import ast; ast.parse(open(\'bot/__init__.py\').read()); print(\'OK\')"', 'Syntax check refactored');
  await sshRun('cd /root/staging/bot_src && python3 -c "import ast; ast.parse(open(\'bot/__init__.py\').read()); print(\'OK\')"', 'Syntax check staging');
  
  // Verify _replit_patch exists now
  await sshRun("grep -c '_replit_patch' /root/Sales-Tele-Bot_refactored/bot/__init__.py", '_replit_patch count refactored');
  await sshRun("grep -c '_replit_patch' /root/staging/bot_src/bot/__init__.py", '_replit_patch count staging');

  console.log('\n✅ DONE');
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
