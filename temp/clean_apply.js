const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Python fix: scoped to step_tu_kpay function
  const pyScript = `path = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(path, 'r') as f:
    lines = f.readlines()

# Find step_tu_kpay function boundaries
fn_start = None
fn_end = None
for i, line in enumerate(lines):
    if 'async def step_tu_kpay' in line:
        fn_start = i
    if fn_start is not None and 'async def step_tu_confirm' in line:
        fn_end = i
        break

# Find markers WITHIN the function
btn_idx = fn_start  # BTN_PAY_DONE comment
review_idx = fn_start  # Show review comment
dead_idx = fn_start  # Try to parse comment (dead code)
dead_end_idx = fn_start  # End of dead code

for i in range(fn_start, fn_end):
    s = lines[i].strip()
    if '# Check if text is BTN_PAY_DONE' in s:
        btn_idx = i
    if btn_idx > fn_start and '# Show review (common for both BTN_PAY_DONE' in s:
        review_idx = i
    if review_idx > fn_start and '# Try to parse as amount for current method' in s:
        dead_idx = i

# Find dead code end: the last non-empty line before fn_end
for i in range(fn_end - 1, dead_idx, -1):
    if lines[i].strip():
        dead_end_idx = i + 1
        break

print(f'fn_start={fn_start+1}, fn_end={fn_end+1}')
print(f'BTN check at line {btn_idx+1}')
print(f'Review at line {review_idx+1}')
print(f'Dead code at line {dead_idx+1} to {dead_end_idx+1}')

# Extract blocks
# Everything before btn (includes cancel/back + method name check)
pre_btn = lines[fn_start:btn_idx]
# BTN_PAY_DONE check block (from btn to review)
btn_block = lines[btn_idx:review_idx]
# Review block (from review to dead)
review_block = lines[review_idx:dead_idx]
# Dead code block (from dead to dead_end)
dead_block = lines[dead_idx:dead_end_idx]

print(f'pre_btn: {len(pre_btn)} lines')
print(f'btn_block: {len(btn_block)} lines')
print(f'review_block: {len(review_block)} lines')
print(f'dead_block: {len(dead_block)} lines')

# Build new function: pre_btn + dead_block + btn_block + review_block
new_func = pre_btn + dead_block + btn_block + review_block
new_lines = lines[:fn_start] + new_func + lines[fn_end:]
new_content = ''.join(new_lines)

with open(path, 'w') as f:
    f.write(new_content)

print(f'Wrote {len(new_content)} chars')

# Verify
import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    import sys; sys.exit(1)

# Verify ordering
fn_s = None
fn_e = None
for i, line in enumerate(new_lines):
    if 'async def step_tu_kpay' in line:
        fn_s = i
    if fn_s is not None and 'async def step_tu_confirm' in line:
        fn_e = i
        break

amt_found = False
btn_found = False
rev_found = False
for i in range(fn_s, fn_e):
    s = new_lines[i].strip()
    if '# Try to parse as amount for current method' in s:
        amt_found = True
        amt_line = i + 1
    if amt_found and '# Check if text is BTN_PAY_DONE' in s:
        btn_found = True
        btn_line = i + 1
    if btn_found and '# Show review (common for both BTN_PAY_DONE' in s:
        rev_found = True
        rev_line = i + 1

if amt_found and btn_found and rev_found:
    print(f'Amount parse: line {amt_line}, BTN: line {btn_line}, Review: line {rev_line}')
    if amt_line < btn_line < rev_line:
        print('ORDER VERIFIED: amount < BTN < review')
    else:
        print(f'BAD ORDER!')
        import sys; sys.exit(1)
else:
    print(f'Missing blocks: amt={amt_found}, btn={btn_found}, rev={rev_found}')
    import sys; sys.exit(1)

# Verify no dead code after return TU_CONFIRM
return_line = None
for i in range(fn_s, fn_e):
    if new_lines[i].strip() == 'return TU_CONFIRM':
        return_line = i
if return_line:
    # Check that nothing meaningful follows before next function
    for j in range(return_line + 1, fn_e):
        s = new_lines[j].strip()
        if s and not s.startswith('@log_duration'):
            if not s.startswith('async def step_tu_confirm'):
                print(f'WARNING: code after return at line {j+1}: {s[:60]}')
    print('No dead code after return TU_CONFIRM')

print('ALL CHECKS PASSED')
`;

  const b64 = Buffer.from(pyScript).toString('base64');
  conn.exec(`echo '${b64}' | base64 -d | python3`, (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    let eout = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { eout += d.toString(); });
    stream.on('close', (code) => {
      console.log('EXIT:', code);
      console.log('STDOUT:', out);
      if (eout) console.log('STDERR:', eout);
      
      if (code === 0) {
        conn.exec("sed -n '1180,1215p' /root/psvibe-sales-bot/bot/handlers/members.py", (err2, s2) => {
          if (err2) { console.error('ERR:', err2); conn.end(); return; }
          let o2 = '';
          s2.on('data', (d) => { o2 += d.toString(); });
          s2.on('close', () => {
            console.log('=== FINAL VERIFY (1180-1215) ===');
            console.log(o2);
            conn.end();
          });
        });
      } else {
        conn.end();
      }
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
