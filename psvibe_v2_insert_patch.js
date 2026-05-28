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
  // Insert _replit_patch into bot/__init__.py
  const pythonScript = `
import re

for fpath in ['/root/Sales-Tele-Bot_refactored/bot/__init__.py', '/root/staging/bot_src/bot/__init__.py']:
    with open(fpath) as f:
        content = f.read()

    # Insert _replit_patch after _replit_delete function (search for the end of that function)
    # Pattern: the closing of _replit_delete function comes right before "def _load_cfg():"
    marker = "def _load_cfg():"

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
        logging.warning("API PATCH /%%s HTTP %%s: %%s", path, e.code, err_body)
        return err_body
    except Exception as e:
        logging.warning("API PATCH /%%s failed: %%s", path, e)
        return None

'''

    if marker in content:
        new_content = content.replace(marker, _replit_patch_code + marker)
        # Only insert once
        with open(fpath, 'w') as f:
            f.write(new_content)
        print(f'INSERTED _replit_patch in {fpath}')
    else:
        print(f'MARKER NOT FOUND in {fpath}')
`;

  await sshRun(`python3 -c "${pythonScript.replace(/'/g, "'\\''").replace(/"/g, '\\"')}"`, 'Insert _replit_patch');
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
