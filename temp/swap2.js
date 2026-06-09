const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Python script that does the swap IN-PLACE on the VPS
const pyScript = `import sys
path = '/root/psvibe-sales-bot/bot/handlers/members.py'

with open(path, 'r') as f:
    content = f.read()

# Block A: BTN_PAY_DONE check
blockA = '    # Check if text is BTN_PAY_DONE\\n    if text == BTN_PAY_DONE:\\n        payments = d.get("tu_payments", {})\\n        psf = sum(payments.values())\\n        if psf <= 0:\\n            await update.message.reply_text("\\\\u26a0\\\\ufe0f \\\\u1021\\\\u1014\\\\u102c\\\\u100a\\\\u1036\\\\u1006\\\\u1031\\\\u1038 payment method \\\\u1010\\\\u1005\\\\u1039 \\\\u1011\\\\u102d\\\\u1004\\\\u1039\\\\u1015\\\\u102b\\\\u1038 -")\\n            return await prompt_tu_kpay(update, context)\\n        d["tu_kpay"] = payments.get("KPay", 0)\\n        d["tu_cash"] = payments.get("Cash", 0)\\n'

# Instead, let's just use simpler markers
# Find the start and end of BTN_PAY_DONE block
a_start = content.find('    # Check if text is BTN_PAY_DONE\\n')
if a_start == -1:
    print('ERROR: BTN_PAY_DONE block not found')
    sys.exit(1)

# Find start of amount parsing block (right after BTN_PAY_DONE block ends)
b_start = content.find('    # Try to parse as amount for current method\\n', a_start)
if b_start == -1:
    print('ERROR: Amount parsing block not found')
    sys.exit(1)

# Find end of amount parsing block (before review section)
c_start = content.find('    # Show review (common for both BTN_PAY_DONE', b_start)
if c_start == -1:
    print('ERROR: Review section not found')
    sys.exit(1)

# Extract both blocks
# Block A: from a_start to b_start
block_a = content[a_start:b_start]
# Block B: from b_start to c_start  
block_b = content[b_start:c_start]

print(f'Block A: {len(block_a)} chars, starts: {repr(block_a[:50])}')
print(f'Block B: {len(block_b)} chars, starts: {repr(block_b[:50])}')

# Swap: put block_b before block_a
new_middle = block_b + block_a
# Content: before a_start + swapped blocks + from c_start
new_content = content[:a_start] + new_middle + content[c_start:]

print(f'New len: {len(new_content)} (was {len(content)})')

# Verify swap
ba_pos = new_content.find('    # Try to parse as amount for current method\\n')
bb_pos = new_content.find('    # Check if text is BTN_PAY_DONE\\n', ba_pos)
rr_pos = new_content.find('    # Show review (common for both BTN_PAY_DONE', bb_pos)

if ba_pos < bb_pos < rr_pos:
    print(f'VERIFIED swap order: amount({ba_pos}) < btn_done({bb_pos}) < review({rr_pos})')
else:
    print(f'BAD ORDER: amount={ba_pos}, btn_done={bb_pos}, review={rr_pos}')
    sys.exit(1)

# Write back
with open(path, 'w') as f:
    f.write(new_content)

# Verify syntax
import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    sys.exit(1)

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
      
      if (code === 0) {
        // Quick verify: read the swapped area
        conn.exec("grep -n '# Check if text is BTN_PAY_DONE\\|# Try to parse as amount\\|# Show review (common for both' /root/psvibe-sales-bot/bot/handlers/members.py | head -10", (err2, s2) => {
          if (err2) { console.error('ERR2:', err2); conn.end(); return; }
          let o2 = '';
          s2.on('data', (d) => { o2 += d.toString(); });
          s2.on('close', () => {
            console.log('=== MARKER POSITIONS AFTER FIX ===');
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
