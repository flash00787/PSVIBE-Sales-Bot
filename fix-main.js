const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  // Rewrite main.py to simply use V1's battle-tested main() from _v1_compat
  const newMain = `"""PS VIBE Customer Bot (V2 Module) — Entry Point.
Delegates to _v1_compat.main() which contains the production-hardened V1 logic.
"""
import sys, os
# Ensure the customer_bot package directory is on sys.path so
# _v1_compat module can be imported by its own internal imports
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_pkg_dir)
for _d in (_pkg_dir, _parent_dir):
    if _d not in sys.path:
        sys.path.insert(0, _d)

if __name__ == '__main__':
    import _v1_compat
    _v1_compat.main()
`;

  conn.exec(`cat > /root/psvibe_sales_bot/customer_bot/main.py << 'MAINEOF'
"""PS VIBE Customer Bot (V2 Module) — Entry Point.
Delegates to _v1_compat.main() which contains the production-hardened V1 logic.
"""
import sys, os
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_pkg_dir)
for _d in (_pkg_dir, _parent_dir):
    if _d not in sys.path:
        sys.path.insert(0, _d)

if __name__ == '__main__':
    import _v1_compat
    _v1_compat.main()
MAINEOF
echo "main.py rewritten"`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log(out);
      // Restart the customer bot
      conn.exec('systemctl restart psvibe_customer_bot && sleep 3 && systemctl status psvibe_customer_bot --no-pager | head -15 && echo "===LOGS===" && journalctl -u psvibe_customer_bot --no-pager -n 10', (err2, stream2) => {
        let out2 = '';
        stream2.on('data', d => out2 += d.toString());
        stream2.stderr.on('data', d => out2 += d.toString());
        stream2.on('close', () => { console.log(out2); conn.end(); });
      });
    });
  });
});
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8') });
