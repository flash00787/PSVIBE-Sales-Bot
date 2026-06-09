const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Restore from git then apply fix with a DIFFERENT approach
  conn.exec('cd /root/psvibe-sales-bot && git checkout bot/handlers/members.py', (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log('Restore:', out.trim(), 'exit:', code);
      
      // Now use a Python script that identifies the CORRECT markers
      // by using additional context: the amount parsing in step_tu_kpay 
      // is specifically AFTER 'return TU_CONFIRM' (dead code)
      const pyScript = `with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'r') as f:
    lines = f.readlines()

# Find the dead code: '# Try to parse as amount' that comes right after 'return TU_CONFIRM'
dead_start = None
dead_end = None
btn_done_start = None
btn_done_end = None
review_start = None

for i, line in enumerate(lines):
    s = line.strip()
    
    # Find BTN_PAY_DONE section start
    if s.startswith('# Check if text is BTN_PAY_DONE'):
        btn_done_start = i
    
    # Set end of BTN_PAY_DONE section
    if btn_done_start is not None and btn_done_end is None:
        if s == '# Try to parse as amount for current method':
            btn_done_end = i
            dead_start = i
    
    # Find end of dead code (amount parsing)
    if dead_start is not None and dead_end is None:
        if s.startswith('# Show review (common for both BTN_PAY_DONE'):
            dead_end = i
            review_start = i

if None in (dead_start, dead_end, btn_done_start, btn_done_end, review_start):
    print(f'ERROR: dead_start={dead_start}, dead_end={dead_end}, btn_start={btn_done_start}, btn_end={btn_done_end}, review={review_start}')
    import sys; sys.exit(1)

print(f'BTN_PAY_DONE: lines {btn_done_start+1}-{btn_done_end} ({btn_done_end-btn_done_start} lines)')
print(f'Amount parse: lines {dead_start+1}-{dead_end} ({dead_end-dead_start} lines)')
print(f'Review start: line {review_start+1}')

# Extract blocks
btn_done_block = lines[btn_done_start:btn_done_end]
amount_block = lines[dead_start:dead_end]

# Verify review comment follows amount block directly
assert lines[dead_end].strip().startswith('# Show review'), f'Expected review at {dead_end}, got: {lines[dead_end][:50]}'

# Build new file: swap the two blocks
# Before btn_done_start | btn_done_block | amount_block | review+
# After  btn_done_start | amount_block | btn_done_block | review+
new_lines = lines[:btn_done_start] + amount_block + btn_done_block + lines[review_start:]
new_content = ''.join(new_lines)

with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'w') as f:
    f.write(new_content)

print(f'Wrote {len(new_content)} chars')

# Verify syntax
import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    import sys; sys.exit(1)

# Verify structure
nl = new_content.split('\\n')
func_started = False
found_amount = False
found_btn = False
found_review = False
for i, line in enumerate(nl):
    if 'def step_tu_kpay' in line:
        func_started = True
    elif func_started and 'def step_tu_confirm' in line:
        if not (found_amount and found_btn and found_review):
            print('ERROR: Missing blocks')
            import sys; sys.exit(1)
        break
    elif func_started and line.strip().startswith('# Try to parse as amount for current method'):
        found_amount = True
        print(f'Amount parse at line {i+1}')
    elif func_started and line.strip().startswith('# Check if text is BTN_PAY_DONE'):
        found_btn = True
        print(f'BTN_PAY_DONE at line {i+1}')
    elif func_started and line.strip().startswith('# Show review (common for both BTN_PAY_DONE'):
        found_review = True
        print(f'Review at line {i+1}')

print('ALL CHECKS PASSED')
`;

      const b64 = Buffer.from(pyScript).toString('base64');
      
      conn.exec(`echo '${b64}' | base64 -d | python3`, (err2, stream2) => {
        if (err2) { console.error('ERR2:', err2); conn.end(); return; }
        let out2 = '';
        let err2out = '';
        stream2.on('data', (d) => { out2 += d.toString(); });
        stream2.stderr.on('data', (d) => { err2out += d.toString(); });
        stream2.on('close', (code2) => {
          console.log('EXIT:', code2);
          console.log('STDOUT:', out2);
          if (err2out) console.log('STDERR:', err2out);
          
          // Also verify the final structure
          conn.exec("sed -n '1170,1220p' /root/psvibe-sales-bot/bot/handlers/members.py", (err3, s3) => {
            if (err3) { console.error('ERR3:', err3); conn.end(); return; }
            let o3 = '';
            s3.on('data', (d) => { o3 += d.toString(); });
            s3.on('close', () => {
              console.log('=== FINAL (1170-1220) ===');
              console.log(o3);
              conn.end();
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
