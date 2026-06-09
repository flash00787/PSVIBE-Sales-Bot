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
      console.log('Reset');
      
      const pyScript = `path = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(path, 'r') as f:
    content = f.read()

# Scope to step_tu_kpay
tu_s = content.find('async def step_tu_kpay')
tu_e = content.find('async def step_tu_confirm', tu_s)
body = content[tu_s:tu_e]

# 1. Find dead code (after return TU_CONFIRM, before end of this function)
dead_marker = '    return TU_CONFIRM\\n\\n    # Try to parse as amount for current method'
dead_start_rel = body.find(dead_marker)
if dead_start_rel == -1:
    print('ERROR: dead code not found')
    import sys; sys.exit(1)
dead_start_rel += len('    return TU_CONFIRM\\n')

# Find the END of the dead code: the line before the close of the function
# The dead code ends with the LAST 'return await prompt_tu_kpay(update, context)' before end of body
dead_end_marker = '    return await prompt_tu_kpay(update, context)\\n'
# Use rfind to get the LAST occurrence in the body
dead_return_rel = body.rfind(dead_end_marker, dead_start_rel)
if dead_return_rel == -1:
    print('ERROR: dead code end not found')
    import sys; sys.exit(1)
dead_end_rel = dead_return_rel + len(dead_end_marker)

dead_block = body[dead_start_rel:dead_end_rel]
print(f'Dead block: {len(dead_block)} chars')
print(f'Ends with: {repr(dead_block[-80:])}')

# Verify the block is complete
if '    if "tu_payments" not in d:' in dead_block and 'd["tu_payments"][current_method] = method_amt' in dead_block:
    print('Dead block contains full amount parsing logic')
else:
    print('WARNING: Dead block may be truncated')

# 2. Remove dead code from body
body_no_dead = body[:dead_start_rel] + body[dead_end_rel:]

# 3. Insert before BTN_PAY_DONE check
btn_marker = '    # Check if text is BTN_PAY_DONE\\n'
btn_p = body_no_dead.find(btn_marker)
insert_marker = '        return TU_KPAY\\n\\n    # Check if text is BTN_PAY_DONE'
ins_rel = body_no_dead.rfind(insert_marker, 0, btn_p + len(btn_marker))
if ins_rel == -1:
    print('ERROR: insert point not found')
    import sys; sys.exit(1)
ins_p = ins_rel + len('        return TU_KPAY\\n')

# Insert dead block
new_body = body_no_dead[:ins_p] + dead_block + body_no_dead[ins_p:]

# Rebuild
new_content = content[:tu_s] + new_body + content[tu_e:]
with open(path, 'w') as f:
    f.write(new_content)

# Verify syntax
import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    import sys; sys.exit(1)

# Verify structure
tu_s2 = new_content.find('async def step_tu_kpay')
tu_e2 = new_content.find('async def step_tu_confirm', tu_s2)
sec = new_content[tu_s2:tu_e2]

amt = sec.find('\\n    # Try to parse as amount for current method\\n')
btn = sec.find('\\n    # Check if text is BTN_PAY_DONE\\n')
rev = sec.find('\\n    # Show review (common for both BTN_PAY_DONE')
ret_confirm = sec.rfind('    return TU_CONFIRM\\n')

print(f'Amt: {amt}, BTN: {btn}, Rev: {rev}, Return: {ret_confirm}')

# Verify order
if amt < btn < rev < ret_confirm:
    print('PERFECT ORDER: amount < BTN < review < return TU_CONFIRM')
elif amt < btn:
    print('GOOD: amount < BTN')
else:
    print(f'BAD ORDER: amt={amt}, btn={btn}')
    import sys; sys.exit(1)

# Verify no dead code after return TU_CONFIRM
after_ret = sec[ret_confirm + len('    return TU_CONFIRM\\n'):]
if '    # Try to parse as amount' in after_ret:
    print('ERROR: Dead code after return')
    import sys; sys.exit(1)

# But there should be nothing significant before next function/end
# (maybe blank lines or the function end)
significant = [l.strip() for l in after_ret.split('\\n') if l.strip() and not l.strip().startswith('@log_duration')]
if significant:
    print(f'WARNING: Content after return TU_CONFIRM: {significant[:3]}')
else:
    print('Clean: nothing after return TU_CONFIRM')

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
            // Full verification
            conn.exec("echo '=== ORDER ===' && grep -n '# Try to parse as amount\\|# Check if text is BTN_PAY_DONE\\|# Show review (common\\|return TU_CONFIRM' /root/psvibe-sales-bot/bot/handlers/members.py | sed -n '/step_tu_kpay/,/step_tu_confirm/p' | head -20 && echo '=== RETURN AREA ===' && sed -n '1260,1280p' /root/psvibe-sales-bot/bot/handlers/members.py && echo '=== SYNTAX ===' && cd /root/psvibe-sales-bot && python3 -c \"import ast; ast.parse(open('bot/handlers/members.py').read()); print('FINAL SYNTAX OK')\"", (err3, s3) => {
              if (err3) { console.error('ERR:', err3); conn.end(); return; }
              let o3 = '';
              s3.on('data', (d) => { o3 += d.toString(); });
              s3.on('close', () => {
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
