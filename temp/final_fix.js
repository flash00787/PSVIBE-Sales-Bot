const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Simple approach: use line numbers from the known structure
// Dead code: lines 1249-1272, review section starts at line 1192
// Move lines 1249-1272 to after line 1191 (before review section)
const pyScript = `with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'r') as f:
    lines = f.readlines()

# Known positions from original file
# Return TU_CONFIRM is followed by dead code
# Find the exact dead code boundaries
dead_start = None
dead_end = None
review_start = None

for i, line in enumerate(lines):
    if line.strip().startswith('# Show review (common for both BTN_PAY_DONE'):
        review_start = i
    if dead_start is None and line.strip() == '# Try to parse as amount for current method':
        # This is the dead code start - but only if it comes after return TU_CONFIRM
        # Check the line before is blank and the line before that is return TU_CONFIRM
        if i >= 1 and lines[i-1].strip() == '' and i >= 2 and lines[i-2].strip() == 'return TU_CONFIRM':
            dead_start = i
    if dead_start is not None and dead_end is None and line.strip().startswith('@log_duration'):
        dead_end = i
        break

if dead_start is None or dead_end is None or review_start is None:
    print(f'ERROR: dead_start={dead_start}, dead_end={dead_end}, review_start={review_start}')
    exit(1)

print(f'Dead code: lines {dead_start+1}-{dead_end} ({dead_end-dead_start} lines)')
print(f'Review starts: line {review_start+1}')

# Extract dead block
dead_block = lines[dead_start:dead_end]

# Build new content:
# lines[0:dead_start] - everything up to dead code (includes the blank line separator)
# lines[dead_end:] - everything after dead code
# Then insert dead_block before review_start (adjusted for removal)

# First remove dead code
new_lines = lines[:dead_start] + lines[dead_end:]

# Adjust review_start since we removed lines before it
# dead_start < dead_end, and review_start < dead_start
# So review_start doesn't change

# Insert dead block before review section
new_lines = new_lines[:review_start] + dead_block + new_lines[review_start:]

new_content = ''.join(new_lines)

with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'w') as f:
    f.write(new_content)

print(f'Wrote {len(new_content)} chars ({len(new_lines)} lines)')

# Verify
import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    exit(1)

# Verify structure of step_tu_kpay function
new_lines_check = new_content.split('\\n')
in_func = False
after_return = False
for i, line in enumerate(new_lines_check):
    if 'def step_tu_kpay' in line:
        in_func = True
        after_return = False
    elif in_func and 'def step_tu_confirm' in line:
        break
    elif in_func and line.strip() == 'return TU_CONFIRM':
        after_return = True
    elif in_func and after_return and line.strip().startswith('# Try to parse'):
        print(f'ERROR: Dead code after return at line {i+1}')
        exit(1)
    elif in_func and not after_return and line.strip().startswith('# Try to parse'):
        print(f'Amount parsing at line {i+1} (before return - CORRECT)')
    elif in_func and not after_return and line.strip().startswith('# Show review'):
        print(f'Review section at line {i+1}')
    elif in_func and after_return and line.strip().startswith('@log_duration'):
        print('Next function found after return - no dead code')
        break

print('ALL CHECKS PASSED')
`;

const b64 = Buffer.from(pyScript).toString('base64');

conn.on('ready', () => {
  console.log('SSH connected');
  
  const cmd = `echo '${b64}' | base64 -d | python3`;
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); return; }
    let out = '';
    let stderrOut = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { stderrOut += d.toString(); });
    stream.on('close', (code) => {
      console.log('EXIT:', code);
      console.log('STDOUT:', out);
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
