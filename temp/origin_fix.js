const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Restore from ORIGINAL (origin) not the local index
  conn.exec('cd /root/psvibe-sales-bot && git checkout origin/master -- bot/handlers/members.py 2>&1 || echo "FALLBACK"; git stash 2>/dev/null; git checkout origin/master -- bot/handlers/members.py 2>&1', (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log('Restore:', out.trim());
      
      // Verify it's the original
      conn.exec("grep -n 'step_tu_kpay\\|# Try to parse as amount\\|# Check if text is BTN_PAY_DONE\\|# Show review (common for both.*BTN_PAY_DONE' /root/psvibe-sales-bot/bot/handlers/members.py | head -20", (err2, s2) => {
        if (err2) { console.error('ERR2:', err2); conn.end(); return; }
        let o2 = '';
        s2.on('data', (d) => { o2 += d.toString(); });
        s2.on('close', () => {
          console.log('=== ORIGINAL MARKERS ===');
          console.log(o2);
          console.log('=== END ===');
          
          // Now apply the fix using PYTHON on the VPS with line-based approach
          // The key: use function boundaries to disambiguate
          const pyScript = `path = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(path, 'r') as f:
    content = f.read()

lines = content.split('\\n')

# Find step_tu_kpay function boundaries
_tu_kpay_start = None
_tu_confirm_start = None
for i, line in enumerate(lines):
    if 'async def step_tu_kpay' in line:
        _tu_kpay_start = i
    if _tu_kpay_start is not None and 'async def step_tu_confirm' in line:
        _tu_confirm_start = i
        break

if _tu_kpay_start is None or _tu_confirm_start is None:
    print(f'ERROR: functions not found: tu_kpay={_tu_kpay_start}, tu_confirm={_tu_confirm_start}')
    import sys; sys.exit(1)

print(f'step_tu_kpay starts at line {_tu_kpay_start+1}')
print(f'step_tu_confirm starts at line {_tu_confirm_start+1}')

# Now find markers ONLY within step_tu_kpay function
btn_start = None
amt_start = None
review_start = None

for i in range(_tu_kpay_start, _tu_confirm_start):
    s = lines[i].strip()
    if '# Check if text is BTN_PAY_DONE' in s:
        btn_start = i
    if btn_start is not None and amt_start is None and '# Try to parse as amount' in s:
        amt_start = i
    if amt_start is not None and review_start is None and '# Show review (common for both BTN_PAY_DONE' in s:
        review_start = i
        break

print(f'BTN_PAY_DONE block: line {btn_start+1}')
print(f'Amount parse block: line {amt_start+1}')
print(f'Review section: line {review_start+1}')

if None in (btn_start, amt_start, review_start):
    print('ERROR: missing markers')
    import sys; sys.exit(1)

# Extract blocks
btn_block = lines[btn_start:amt_start]
amt_block = lines[amt_start:review_start]

print(f'BTN block: {len(btn_block)} lines')
print(f'AMT block: {len(amt_block)} lines')

# Swap: put amount parsing before BTN_PAY_DONE
new_func_lines = lines[_tu_kpay_start:btn_start] + amt_block + btn_block + lines[review_start:_tu_confirm_start]
new_lines = lines[:_tu_kpay_start] + new_func_lines + lines[_tu_confirm_start:]
new_content = '\\n'.join(new_lines)

with open(path, 'w') as f:
    f.write(new_content)

print(f'Wrote {len(new_content)} chars')

import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    import sys; sys.exit(1)

# Verify ordering within function
for i, line in enumerate(new_lines):
    if 'async def step_tu_kpay' in line:
        fn_start = i
    elif fn_start and 'async def step_tu_confirm' in line:
        break
    elif fn_start and '# Try to parse as amount' in line:
        amt_pos = i
        print(f'Amount parse: line {i+1}')
    elif fn_start and '# Check if text is BTN_PAY_DONE' in line:
        btn_pos = i
        print(f'BTN check: line {i+1}')
    elif fn_start and '# Show review (common for both BTN_PAY_DONE' in line:
        rev_pos = i
        print(f'Review: line {i+1}')

if amt_pos < btn_pos < rev_pos:
    print('ORDER VERIFIED: amount < BTN < review')
else:
    print(f'BAD ORDER: amt={amt_pos}, btn={btn_pos}, rev={rev_pos}')
    import sys; sys.exit(1)

print('ALL CHECKS PASSED')
`;

          const b64 = Buffer.from(pyScript).toString('base64');
          conn.exec(`echo '${b64}' | base64 -d | python3`, (err3, s3) => {
            if (err3) { console.error('ERR3:', err3); conn.end(); return; }
            let o3 = '';
            let e3 = '';
            s3.on('data', (d) => { o3 += d.toString(); });
            s3.stderr.on('data', (d) => { e3 += d.toString(); });
            s3.on('close', (code3) => {
              console.log('FIX EXIT:', code3);
              console.log('STDOUT:', o3);
              if (e3) console.log('STDERR:', e3);
              
              if (code3 === 0) {
                conn.exec("sed -n '1188,1215p' /root/psvibe-sales-bot/bot/handlers/members.py", (err4, s4) => {
                  if (err4) { console.error('ERR4:', err4); conn.end(); return; }
                  let o4 = '';
                  s4.on('data', (d) => { o4 += d.toString(); });
                  s4.on('close', () => {
                    console.log('=== VERIFY SWAP (1188-1215) ===');
                    console.log(o4);
                    conn.end();
                  });
                });
              } else {
                conn.end();
              }
            });
          });
        });
      });
    });
  });
});

conn.on('error', (err) => { console.error('SSH ERROR:', err); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
