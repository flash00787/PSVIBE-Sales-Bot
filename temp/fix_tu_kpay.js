const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const fixScript = `import re

with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'r') as f:
    lines = f.readlines()

# Find markers
tu_confirm_idx = None
dead_start_idx = None
dead_end_idx = None
review_idx = None

for i, line in enumerate(lines):
    s = line.strip()
    if s == 'return TU_CONFIRM':
        # Check next non-blank lines for dead code marker
        for j in range(i+1, min(i+5, len(lines))):
            if lines[j].strip().startswith('# Try to parse as amount'):
                tu_confirm_idx = i
                dead_start_idx = j
                break
    if s.startswith('# Show review (common for both BTN_PAY_DONE'):
        review_idx = i
    if dead_start_idx is not None and dead_end_idx is None:
        if s.startswith('@log_duration'):
            dead_end_idx = i

print(f"return TU_CONFIRM: line {tu_confirm_idx + 1 if tu_confirm_idx else 'N/A'}")
print(f"Dead code start:   line {dead_start_idx + 1 if dead_start_idx else 'N/A'}")
print(f"Dead code end:     line {dead_end_idx + 1 if dead_end_idx else 'N/A'}")
print(f"Review section:    line {review_idx + 1 if review_idx else 'N/A'}")

if None in (tu_confirm_idx, dead_start_idx, dead_end_idx, review_idx):
    print("ERROR: Could not find all markers")
    exit(1)

# Extract dead code block
dead_block = lines[dead_start_idx:dead_end_idx]
print(f"Dead code: {len(dead_block)} lines")

# Step 1: Remove dead code from original position
# Keep everything up to dead_start_idx, then skip to dead_end_idx
new_lines = lines[:dead_start_idx] + lines[dead_end_idx:]
print(f"After removal: {len(new_lines)} lines (was {len(lines)})")

# Step 2: Insert dead code BEFORE review section
# review_idx doesn't shift (dead code was after it)
before = new_lines[:review_idx]
after = new_lines[review_idx:]
new_lines = before + dead_block + after

new_content = ''.join(new_lines)
print(f"After insert: {len(new_lines)} lines")

# Write back
with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'w') as f:
    f.write(new_content)

print('Fix written')

# Verify syntax
import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    exit(1)

# Verify: no unreachable code after return TU_CONFIRM within step_tu_kpay
new_lines_check = new_content.split('\\n')
found_confirm = False
in_step_tu_kpay = False
for i, line in enumerate(new_lines_check):
    if 'def step_tu_kpay' in line:
        in_step_tu_kpay = True
        found_confirm = False
    if in_step_tu_kpay and line.strip() == 'return TU_CONFIRM':
        found_confirm = True
        continue
    if found_confirm and line.strip().startswith('# Try to parse as amount'):
        print(f'ERROR: Dead code still after return TU_CONFIRM at approx line {i+1}')
        exit(1)
    if in_step_tu_kpay and line.strip().startswith('@log_duration'):
        break

# Verify: amount parsing IS before review
review_pos = new_content.find('# Show review (common for both BTN_PAY_DONE')
amount_pos = new_content.find('# Try to parse as amount for current method')
if amount_pos < review_pos:
    print('VERIFIED: Amount parsing is BEFORE review section')
else:
    print(f'ERROR: Amount parsing ({amount_pos}) not before review ({review_pos})')
    exit(1)

# Verify: return TU_CONFIRM is still the last statement before next function
# Find position of return TU_CONFIRM in the function
confirm_pos = new_content.find('return TU_CONFIRM', review_pos)
next_func_pos = new_content.find('@log_duration', review_pos)
if confirm_pos < next_func_pos:
    print('VERIFIED: return TU_CONFIRM is last in function')
else:
    print('WARNING: return TU_CONFIRM may not be last')

print('ALL CHECKS PASSED')
`;

const b64 = Buffer.from(fixScript).toString('base64');

conn.on('ready', () => {
  console.log('SSH connected');
  
  const cmd = `echo '${b64}' | base64 -d | python3`;
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); return; }
    let output = '';
    let stderrOut = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { stderrOut += data.toString(); });
    stream.on('close', (code) => {
      console.log('EXIT:', code);
      console.log('STDOUT:', output);
      if (stderrOut) console.log('STDERR:', stderrOut);
      conn.end();
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
