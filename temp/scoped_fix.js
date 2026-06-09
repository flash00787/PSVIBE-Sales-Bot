const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Reset to clean state
  conn.exec('cd /root/psvibe-sales-bot && git checkout HEAD -- bot/handlers/members.py', (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.on('close', () => {
      console.log('Reset:', out.trim());
      
      const pyScript = `path = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(path, 'r') as f:
    content = f.read()

# Scope: only within step_tu_kpay (after its def line)
tu_kpay_start = content.find('async def step_tu_kpay')
if tu_kpay_start == -1:
    print('ERROR: step_tu_kpay not found')
    import sys; sys.exit(1)

tu_confirm_start = content.find('async def step_tu_confirm', tu_kpay_start)
if tu_confirm_start == -1:
    print('ERROR: step_tu_confirm not found')
    import sys; sys.exit(1)

# Extract the function body
func_body = content[tu_kpay_start:tu_confirm_start]

# 1. Find the dead code block (after return TU_CONFIRM, before end of function)
dead_marker = '    return TU_CONFIRM\\n\\n    # Try to parse as amount for current method'
dead_pos = func_body.find(dead_marker)
if dead_pos == -1:
    print('ERROR: Cannot find dead code in step_tu_kpay')
    import sys; sys.exit(1)

# Skip the 'return TU_CONFIRM' line + following blank line
dead_start = dead_pos + len('    return TU_CONFIRM\\n')

# Find end of dead code (last non-decorator line in the function body)
# The dead code ends with 'return await prompt_tu_kpay(update, context)'
dead_marker_end = '    return await prompt_tu_kpay(update, context)\\n'
dead_end_rel = func_body.find(dead_marker_end, dead_start)
if dead_end_rel == -1:
    print('ERROR: Cannot find end of dead code')
    import sys; sys.exit(1)
dead_end = dead_end_rel + len(dead_marker_end)

# Extract dead code block (from blank line after return TU_CONFIRM through the amount parsing return)
dead_block = func_body[dead_start:dead_end]
print(f'Dead block: {len(dead_block)} chars')
print(f'Starts: {repr(dead_block[:80])}')
print(f'Ends: {repr(dead_block[-80:])}')

# 2. Find insertion point: between the method-name-check's return TU_KPAY and BTN_PAY_DONE check
# This is the LAST return TU_KPAY that precedes '# Check if text is BTN_PAY_DONE' within this function
btn_marker = '    # Check if text is BTN_PAY_DONE\\n'
btn_pos = func_body.find(btn_marker)
if btn_pos == -1:
    print('ERROR: Cannot find BTN_PAY_DONE in step_tu_kpay')
    import sys; sys.exit(1)

# Find the return TU_KPAY that immediately precedes BTN_PAY_DONE
insert_marker = '        return TU_KPAY\\n\\n    # Check if text is BTN_PAY_DONE'
insert_pos_rel = func_body.rfind(insert_marker, 0, btn_pos + len(btn_marker))
if insert_pos_rel == -1:
    print('ERROR: Cannot find insertion point')
    import sys; sys.exit(1)

insert_pos = insert_pos_rel + len('        return TU_KPAY\\n')
print(f'Insertion point found at relative pos {insert_pos}')

# 3. Build new function body: remove dead + insert at new position
# First remove dead code
func_no_dead = func_body[:dead_start] + func_body[dead_end:]

# Adjust insertion point (dead code was removed, but it was AFTER insert_pos)
# dead_start > insert_pos, so insert_pos doesn't change

# Insert dead_block at insert_pos
new_func_body = func_no_dead[:insert_pos] + dead_block + func_no_dead[insert_pos:]

# 4. Rebuild full file
new_content = content[:tu_kpay_start] + new_func_body + content[tu_confirm_start:]

with open(path, 'w') as f:
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

# Verify ordering within step_tu_kpay
tu_s = new_content.find('async def step_tu_kpay')
tu_e = new_content.find('async def step_tu_confirm', tu_s)
section = new_content[tu_s:tu_e]

amt_p = section.find('    # Try to parse as amount for current method\\n')
btn_p = section.find('    # Check if text is BTN_PAY_DONE\\n')
rev_p = section.find('    # Show review (common for both BTN_PAY_DONE')
ret_p = section.find('    return TU_CONFIRM\\n')

print(f'Amount: {amt_p}, BTN: {btn_p}, Review: {rev_p}, Return TU_CONFIRM: {ret_p}')
if amt_p != -1 and btn_p != -1 and amt_p < btn_p:
    print('VERIFIED: Amount parsing BEFORE BTN_PAY_DONE')
else:
    print(f'ORDER ERROR: amt={amt_p}, btn={btn_p}')
    import sys; sys.exit(1)

# Verify no dead code after return TU_CONFIRM  
after_ret = section[ret_p + len('    return TU_CONFIRM\\n'):]
if '# Try to parse as amount' in after_ret.split('async def step_tu_confirm')[0]:
    print('ERROR: Dead code after return TU_CONFIRM')
    import sys; sys.exit(1)
print('VERIFIED: No dead code after return TU_CONFIRM')
print('ALL CHECKS PASSED')
`;

      const b64 = Buffer.from(pyScript).toString('base64');
      conn.exec(`echo '${b64}' | base64 -d | python3`, (err2, s2) => {
        if (err2) { console.error('ERR:', err2); conn.end(); return; }
        let o2 = '';
        let e2 = '';
        s2.on('data', (d) => { o2 += d.toString(); });
        s2.stderr.on('data', (d) => { e2 += d.toString(); });
        s2.on('close', (code) => {
          console.log('EXIT:', code);
          console.log('STDOUT:', o2);
          if (e2) console.log('STDERR:', e2);
          
          if (code === 0) {
            conn.exec("sed -n '1180,1218p' /root/psvibe-sales-bot/bot/handlers/members.py && echo '---RETURN AREA---' && sed -n '1255,1275p' /root/psvibe-sales-bot/bot/handlers/members.py", (err3, s3) => {
              if (err3) { console.error('ERR:', err3); conn.end(); return; }
              let o3 = '';
              s3.on('data', (d) => { o3 += d.toString(); });
              s3.on('close', () => {
                console.log('=== VERIFICATION ===');
                console.log(o3);
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

conn.on('error', (err) => { console.error('SSH ERROR:', err); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
