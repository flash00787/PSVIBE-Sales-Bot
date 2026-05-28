const { Client } = require('ssh2');
const fs = require('fs');
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const DIR = '/root/Aung Chan Myint/Sales-Tele-Bot';
const VPS = '5.223.81.16';

function ssh(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client(); let out = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => out += d.toString());
        stream.on('close', () => { conn.end(); resolve(out); });
      });
    }).on('error', e => { conn.end(); reject(e); })
    .connect({ host: VPS, username: 'root',
      privateKey: fs.readFileSync(KEY), readyTimeout: 30000 });
  });
}

(async () => {
  // Step 1: Gather diagnostics
  console.log('=== STEP 1: DIAGNOSTICS ===');
  
  // Check try/except balance in main.py
  let r = await ssh('python3 -c "'
    + 'with open(\'' + DIR + '/main.py\') as f: lines = f.readlines();'
    + 'stack=[]; orphans=[];'
    + 'for i,line in enumerate(lines):'
    + '  s=line.strip();'
    + '  if s==\'try:\': stack.append((\'try\',i+1));'
    + '  if s.startswith(\'except \'): '
    + '    if stack and stack[-1][0]==\'try\': stack.pop();'
    + '    else: orphans.append((\'except\',i+1));'
    + '  if s==\'finally:\' or s.startswith(\'else:\'):'
    + '    if stack and stack[-1][0]==\'try\': stack.pop();'
    + 'print(f\'Open tries: {len(stack)}\');'
    + 'for k,n in stack: print(f\'  Line {n}: {k}\');'
    + 'print(f\'Orphan excepts: {len(orphans)}\');'
    + 'for k,n in orphans: print(f\'  Line {n}: {k}\');'
    + '" 2>&1');
  console.log('Try/except balance:');
  console.log(r);

  // Check _replit functions  
  r = await ssh('grep -n "def _replit" "' + DIR + '/bot/__init__.py"');
  console.log('\nReplit functions in bot/__init__.py:\n' + r);

  r = await ssh('grep -c "_replit_patch" "' + DIR + '/bot/handlers.py"');
  console.log('\n_replit_patch usages in handlers.py: ' + r.trim());

  // Show main.py _replit_patch
  r = await ssh('sed -n "8328,8365p" "' + DIR + '/main.py"');
  console.log('\nmain.py _replit_patch definition:\n' + r);

  // Step 2: Fix _replit_patch missing from bot/__init__.py
  console.log('\n=== STEP 2: ADD _replit_patch TO bot/__init__.py ===');
  
  // Add _replit_patch after _replit_post  
  let patchFunc = `
def _replit_patch(path: str, body: dict):
    """PATCH request to the internal API server."""
    try:
        url = _api_base() + '/api/' + path
        data = json.dumps(body).encode('utf-8')
        req = Request(url, data=data, method='PATCH')
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-API-Key', _API_KEY)
        with urlopen(req, timeout=8) as resp:
            if resp.status == 409:
                return {'conflict': True}
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logging.warning('_replit_patch(%s): %s', path, e)
        return None
`;

  // Use Python to find where to insert
  r = await ssh('grep -n "def _replit_post\\|def _replit_delete\\|def _replit_get" "' + DIR + '/bot/__init__.py"');
  console.log('Insert points:\n' + r);

  // Insert _replit_patch after _replit_post (line from grep)
  let lines = r.trim().split('\n');
  let postLine = null;
  for (let l of lines) {
    if (l.includes('def _replit_post')) {
      postLine = parseInt(l.split(':')[0]);
    }
  }
  
  if (postLine) {
    // Find the end of _replit_post function (next def or next blank after function)
    let insertCmd = "sed -i '" + (postLine + 1) + "r /dev/stdin' \"" + DIR + "/bot/__init__.py\" << 'FUNCMARK'\n";
    insertCmd += patchFunc;
    insertCmd += "FUNCMARK";
    
    r = await ssh(insertCmd);
    console.log('Insert result (should be empty on success): ' + r);
    
    // Verify
    r = await ssh('grep -n "def _replit_patch" "' + DIR + '/bot/__init__.py"');
    console.log('Verification:\n' + r);
    
    // Check __all__ needs update
    r = await ssh('grep "_replit_patch" "' + DIR + '/bot/__init__.py"');
    console.log('All _replit_patch references now:\n' + r);
  } else {
    console.log('ERROR: Could not find _replit_post line to insert after');
  }
  
  // Step 3: Backup main.py before fixing
  console.log('\n=== STEP 3: BACKUP main.py ===');
  r = await ssh('cp "' + DIR + '/main.py" "' + DIR + '/main.py.bak.pre_fix" && echo "BACKUP OK"');
  console.log(r);

  // Step 4: Fix main.py try/except
  console.log('\n=== STEP 4: FIND THE BROKEN TRY IN main.py ===');
  r = await ssh('python3 -c "'
    + 'with open(\'' + DIR + '/main.py\') as f: lines = f.readlines();'
    + 'stack=[];'
    + 'for i,line in enumerate(lines):'
    + '  s=line.strip();'
    + '  if s==\'try:\': stack.append((\'try\',i+1));'
    + '  if s.startswith(\'except \'): '
    + '    if stack and stack[-1][0]==\'try\': stack.pop();'
    + '  if s==\'finally:\' or s.startswith(\'else:\'):'
    + '    if stack and stack[-1][0]==\'try\': stack.pop();'
    + 'print(\'Open tries:\', [(k,n) for k,n in stack]);'
    + 'for k,n in stack:'
    + '  for l in lines[max(0,n-3):n+2]:'
    + "    print(f'{lines.index(l)+1}: {l.rstrip()}')"
    + '" 2>&1');
  console.log(r);
  
  // Also check the specific problematic area near 6996
  r = await ssh("sed -n '6985,7010p' '" + DIR + "/main.py'");
  console.log('\nContext around line 6985-7010:\n' + r);

  console.log('\n=== FIXES APPLIED ===');
})();
