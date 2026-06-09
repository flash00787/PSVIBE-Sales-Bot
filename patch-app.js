#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Read the local endpoints file
const endpoints = fs.readFileSync('/home/node/.openclaw/workspace/new_game_endpoints.py', 'utf8');

// The Python code to insert
const pythonCode = `
import sys

def main():
    with open('/root/psvibe_api_server/app.py', 'r') as f:
        content = f.read()

    # Remove previous new_game_endpoints import if exists
    content = content.replace('import new_game_endpoints', '# old endpoints import removed')
    content = content.replace('import app as _app_ref', '# old app_ref removed')

    # Find the line before 'import patch_routes' 
    marker = 'import patch_routes'
    idx = content.find(marker)
    if idx == -1:
        print('ERROR: marker not found')
        sys.exit(1)

    # Find beginning of that line
    line_start = content.rfind('\\n', 0, idx) + 1

    # Insert the endpoint definitions before it (inline, not as import)
    # We need to embed the endpoint code in app.py before import patch_routes
    new_code = '''${endpoints.replace(/'/g, "'\\''")}'''

    # Actually, embedding via Python heredoc is fragile. Let me do it differently.
    # Write endpoints to a temp file, then use it.
    print('Using file-based approach')

main()
`.trim();

const scriptContent = endpoints.split('\n').map(line => '    ' + line).join('\n');

// Write a Python script that inserts code into app.py
const fullPython = `
ENDPOINTS = """${endpoints.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')}"""

with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

# Remove old imports
content = content.replace('import new_game_endpoints\\n', '')
content = content.replace('import new_game_endpoints', '')

marker = 'import patch_routes'
idx = content.find(marker)
if idx == -1:
    print('ERROR: marker not found')
else:
    # Find start of line containing marker
    line_start = content.rfind('\\n', 0, idx) + 1
    indent = ''
    # Insert before the marker line
    # Convert \\n back to real newlines
    endpoints_code = ENDPOINTS.replace('\\\\n', '\\n')
    # Filter out the import/from lines that won't work inline
    lines_to_insert = []
    skip_until_empty = False
    for line in endpoints_code.split('\\n'):
        # Skip the module docstring and imports
        if line.startswith('"""') or line.startswith('import ') or line.startswith('from ') or line.startswith('router = '):
            continue
        lines_to_insert.append(line)
    
    insert = '\\n'.join(lines_to_insert)
    new_content = content[:idx] + insert + '\\n\\n' + content[idx:]
    
    with open('/root/psvibe_api_server/app.py', 'w') as f:
        f.write(new_content)
    print('OK: inserted endpoints')
    print(f'Total lines: {new_content.count(chr(10))}')
`.trim();

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`python3 -c '${fullPython.replace(/'/g, "'\\''")}'`, (err, stream) => {
    let out = '';
    stream.on('data', (d) => out += d.toString());
    stream.stderr.on('data', (d) => out += d.toString());
    stream.on('close', (code) => {
      console.log('Exit:', code);
      console.log(out);
      
      // Validate syntax
      conn.exec('cd /root/psvibe_api_server && /root/psvibe_api_server/venv/bin/python3 -c "import py_compile; py_compile.compile(\'app.py\', doraise=True); print(\'Syntax OK\')" 2>&1', (err2, stream2) => {
        let out2 = '';
        stream2.on('data', (d) => out2 += d.toString());
        stream2.stderr.on('data', (d) => out2 += d.toString());
        stream2.on('close', (code2) => { console.log('Validate:', code2, out2); conn.end(); });
      });
    });
  });
});
conn.on('error', (e) => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY, readyTimeout: 15000 });
