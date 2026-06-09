const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Reset to clean state first
  conn.exec('cd /root/psvibe-sales-bot && git checkout HEAD -- bot/handlers/members.py', (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.on('close', () => {
      console.log('Reset:', out.trim());
      
      // Apply fix using Python on VPS - simple text-based cut and paste
      const pyScript = `path = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(path, 'r') as f:
    content = f.read()

# Extract the dead code block (after return TU_CONFIRM, before next function)
# Pattern: return TU_CONFIRM\\n\\n    # Try to parse as amount...\\n    ...\\n    return await prompt_tu_kpay(update, context)
# Followed by: \\n@log_duration("members:step_tu_confirm")

# Find 'return TU_CONFIRM' that's followed by dead code
dead_marker = '    return TU_CONFIRM\\n\\n    # Try to parse as amount for current method'
pos = content.find(dead_marker)
if pos == -1:
    print('ERROR: Cannot find TU_CONFIRM followed by dead code')
    import sys; sys.exit(1)
pos += len('    return TU_CONFIRM\\n')  # Skip to the blank line after return

# Find end of dead code (before @log_duration for step_tu_confirm)
dead_end_marker = '@log_duration("members:step_tu_confirm")'
dead_end = content.find(dead_end_marker, pos)
if dead_end == -1:
    print('ERROR: Cannot find step_tu_confirm')
    import sys; sys.exit(1)

# Back up to the blank line before @log_duration
dead_end = content.rfind('\\n', pos, dead_end)
if dead_end == -1:
    dead_end = content.rfind('\\n', pos, content.find(dead_end_marker))

dead_block = content[pos:dead_end]
print(f'Dead block: {len(dead_block)} chars')
print(f'Starts: {repr(dead_block[:60])}')
print(f'Ends: {repr(dead_block[-60:])}')

# Remove dead code
content_no_dead = content[:pos] + content[dead_end:]

# Find insertion point: between method name check and BTN_PAY_DONE check
# After the method name check (which returns TU_KPAY) and before BTN_PAY_DONE
insert_marker = '        return TU_KPAY\\n\\n    # Check if text is BTN_PAY_DONE'
insert_pos = content_no_dead.find(insert_marker)
if insert_pos == -1:
    print('ERROR: Cannot find insertion point')
    import sys; sys.exit(1)
insert_pos += len('        return TU_KPAY\\n')  # Insert after the return and its newline

# Insert dead block (amount parsing) here
new_content = content_no_dead[:insert_pos] + dead_block + content_no_dead[insert_pos:]

with open(path, 'w') as f:
    f.write(new_content)
print(f'Wrote {len(new_content)} chars (was {len(content)})')

# Verify
import ast
try:
    ast.parse(new_content)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    import sys; sys.exit(1)

# Verify ordering
amt_pos = new_content.find('    # Try to parse as amount for current method\\n')
btn_pos = new_content.find('    # Check if text is BTN_PAY_DONE\\n')
rev_pos = new_content.find('    # Show review (common for both BTN_PAY_DONE')
ret_pos = new_content.find('    return TU_CONFIRM\\n')

print(f'Amount parse: {amt_pos}, BTN check: {btn_pos}, Review: {rev_pos}, Return: {ret_pos}')
if amt_pos < btn_pos < rev_pos < ret_pos:
    print('ORDER VERIFIED: amount < BTN < review < return TU_CONFIRM')
elif amt_pos < btn_pos < rev_pos:
    print('ORDER: amount < BTN < review (return may be within)')
else:
    print(f'BAD ORDER')
    import sys; sys.exit(1)

# Verify no dead code after return TU_CONFIRM
after_return = new_content[ret_pos + len('    return TU_CONFIRM\\n'):]
# Find next decorator or function
next_decorator = after_return.find('@log_duration("members:step_tu_confirm")')
between = after_return[:next_decorator]
if '# Try to parse as amount' in between:
    print('ERROR: Dead code after return')
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
            conn.exec("sed -n '1180,1215p' /root/psvibe-sales-bot/bot/handlers/members.py", (err3, s3) => {
              if (err3) { console.error('ERR:', err3); conn.end(); return; }
              let o3 = '';
              s3.on('data', (d) => { o3 += d.toString(); });
              s3.on('close', () => {
                console.log('=== FINAL (1180-1215) ===');
                console.log(o3);
                
                // Also verify total structure
                conn.exec("cd /root/psvibe-sales-bot && python3 -c \"import ast; ast.parse(open('bot/handlers/members.py').read()); print('FINAL SYNTAX OK')\" && echo '---' && grep -n 'def step_tu_kpay\\|def step_tu_confirm\\|return TU_CONFIRM\\|# Try to parse as amount\\|# Check if text is BTN_PAY_DONE\\|# Show review (common' /root/psvibe-sales-bot/bot/handlers/members.py | grep -A2 -B2 'step_tu_kpay' | head -30", (err4, s4) => {
                  if (err4) { console.error('ERR:', err4); conn.end(); return; }
                  let o4 = '';
                  s4.on('data', (d) => { o4 += d.toString(); });
                  s4.on('close', () => {
                    console.log('=== FINAL STRUCTURE ===');
                    console.log(o4);
                    conn.end();
                  });
                });
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
