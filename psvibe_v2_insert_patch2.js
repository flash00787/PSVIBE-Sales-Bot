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
  // Step 1: Write the Python fix script to VPS
  const pythonScript = `#!/usr/bin/env python3
"""Insert _replit_patch function into __init__.py files."""

_replit_patch_code = '''
def _replit_patch(path: str, body: dict):
    """PATCH JSON to API server. Returns parsed response or None on error.
    On HTTP 409 conflict, returns dict with 'error' key instead of None."""
    base = _api_base()
    if not base:
        return None
    try:
        import urllib.request as _req
        import urllib.error as _err
        data = json.dumps(body).encode()
        req  = _req.Request(
            f"{base}/api/{path}",
            data=data,
            headers={"Content-Type": "application/json", "X-API-Key": _API_KEY},
            method="PATCH",
        )
        with _req.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except _err.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
        except Exception:
            err_body = {"error": f"http_{e.code}"}
        err_body["__status__"] = e.code
        logging.warning("API PATCH /%s HTTP %s: %s", path, e.code, err_body)
        return err_body
    except Exception as e:
        logging.warning("API PATCH /%s failed: %s", path, e)
        return None

'''

for fpath in ['/root/Sales-Tele-Bot_refactored/bot/__init__.py', '/root/staging/bot_src/bot/__init__.py']:
    with open(fpath) as f:
        content = f.read()
    marker = "def _load_cfg():"
    if marker in content and "_replit_patch" not in content:
        new_content = content.replace(marker, _replit_patch_code + marker)
        with open(fpath, 'w') as f:
            f.write(new_content)
        print(f'INSERTED _replit_patch in {fpath}')
    elif "_replit_patch" in content:
        print(f'ALREADY EXISTS in {fpath}')
    else:
        print(f'MARKER NOT FOUND in {fpath}')
`;

  // Write script to VPS
  const escaped = pythonScript.replace(/'/g, "'\\''");
  
  let r = await sshRun(`cat > /tmp/insert_patch.py << 'PYEOF'
${pythonScript}
PYEOF
echo "Script written"`, 'Write Python script');

  // Step 2: Run the script
  r = await sshRun('python3 /tmp/insert_patch.py', 'Run insert script');

  // Step 3: Verify _replit_patch now exists
  r = await sshRun("grep -n '_replit_patch' /root/Sales-Tele-Bot_refactored/bot/__init__.py | head -5", 'Verify refactored');
  r = await sshRun("grep -n '_replit_patch' /root/staging/bot_src/bot/__init__.py | head -5", 'Verify staging');

  // Step 4: Verify syntax
  r = await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import ast; ast.parse(open(\'bot/__init__.py\').read()); print(\'OK\')"', 'Syntax check refactored');
  r = await sshRun('cd /root/staging/bot_src && python3 -c "import ast; ast.parse(open(\'bot/__init__.py\').read()); print(\'OK\')"', 'Syntax check staging');

  console.log('\n✅ DONE');
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
