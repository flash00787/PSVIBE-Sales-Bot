const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`cat > /tmp/has_api.py << 'PYEOF'
import re
with open('/root/psvibe-sale-bot/bot/__init__.py') as f:
    content = f.read()

print("=== _HAS_API setup and imports ===")
for i, line in enumerate(content.split(chr(10))[:50], 1):
    if 'HAS_API' in line or 'api_client' in line or 'import' in line:
        print(f"L{i}: {line}")

print()
print("=== Lines around _HAS_API ===")
idx = content.find('_HAS_API')
if idx >= 0:
    start = max(0, idx - 200)
    end = min(len(content), idx + 500)
    print(content[start:end])

print()
print("=== save_attendance function ===")
idx = content.find('def save_attendance(')
if idx >= 0:
    end = min(len(content), idx + 1200)
    print(content[idx:end])

print()
print("=== Functions that DON'T use API at all ===")
non_api = ['create_booking', 'end_booking', 'cancel_booking', 
           'add_console_game', 'remove_console_game', 'update_game_library_install',
           'add_console_to_setting', 'remove_console_from_setting', 'check_disc_session_conflict']
for fname in non_api:
    idx = content.find(f'def {fname}(')
    if idx >= 0:
        end = min(len(content), idx + 600)
        snippet = content[idx:end]
        has_api = 'api_' in snippet
        has_if_api = 'HAS_API' in snippet
        print(f"  {fname}: has_api_check={has_api}, has_HAS_API_check={has_if_api}")
        # Print first 5 non-docstring lines
        lines = snippet.split(chr(10))
        count = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('"') and not stripped.startswith("'") and not stripped.startswith('#'):
                print(f"    {stripped[:120]}")
                count += 1
                if count >= 8:
                    break
        print()

print("=== set_game_disc_count function ===")
idx = content.find('def set_game_disc_count(')
if idx >= 0:
    end = min(len(content), idx + 800)
    print(content[idx:end])
PYEOF
python3 /tmp/has_api.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      fs.writeFileSync('/home/node/.openclaw/workspace/audit/has_api_detail.txt', result);
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
