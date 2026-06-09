const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`cat > /tmp/api_check.py << 'PYEOF'
import re, os

# Check API server routes for save_attendance, create_booking, etc.
for api_dir in ['/root/psvibe_api_server', '/root/psvibe-sale-bot/api']:
    if not os.path.exists(api_dir):
        continue
    print(f"=== API directory: {api_dir} ===")
    for root, dirs, files in os.walk(api_dir):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                # Find route definitions
                routes = re.findall(r'@\w+\.(?:get|post|put|delete|patch)\\([\'"]([^\'"]+)[\'"]\\)', content)
                if routes:
                    print(f"  {path}:")
                    for r in routes:
                        print(f"    {r}")
                # Also check def lines near routes
                funcs = re.findall(r'async def (\\w+)\\(', content)
                if 'save_attendance' in content or 'create_booking' in content:
                    print(f"  Found key functions in {path}")

# Count total route registrations
print()
print("=== Route Count Summary ===")
total = 0
for api_dir in ['/root/psvibe_api_server', '/root/psvibe-sale-bot/api']:
    if not os.path.exists(api_dir):
        continue
    for root, dirs, files in os.walk(api_dir):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                routes = re.findall(r'@\w+\.(?:get|post|put|delete|patch)\\(', content)
                total += len(routes)
print(f"Total route decorators found: {total}")

# Check how the API server implements save_attendance  
print()
print("=== Searching for save_attendance in API server ===")
r = __import__('subprocess').run(['grep', '-rn', 'save_attendance', '/root/psvibe_api_server/'], capture_output=True, text=True)
print(r.stdout[:1000] if r.stdout else "Not found in psvibe_api_server")

r = __import__('subprocess').run(['grep', '-rn', 'save_attendance', '/root/psvibe-sale-bot/api/'], capture_output=True, text=True)
print(r.stdout[:1000] if r.stdout else "Not found in psvibe-sale-bot/api/")
PYEOF
python3 /tmp/api_check.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
