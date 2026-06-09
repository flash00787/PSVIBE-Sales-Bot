const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  conn.exec("python3 -c \"\nimport re\n\nwith open('/root/psvibe_api_server/dashboard_routes.py', 'r') as f:\n    content = f.read()\n\n# Fix 1: Remove hardcoded 'category = Food' filter in inventory GET\nold1 = 'where = [\\\"category = \\'Food\\'\\\"]'\nnew1 = 'where = [\\\"1=1\\\"]'\ncontent = content.replace(old1, new1)\n\n# Fix 2: Add payment fields to stock-in POST endpoint\n# Update the variable extraction block\nold2 = '''        item_id = req.get(\\\"item_id\\\")\n        quantity = req.get(\\\"quantity\\\", 0)\n        unit_cost = req.get(\\\"unit_cost\\\", 0)\n        source = req.get(\\\"source\\\", \\\"\\\")\n        receipt_no = req.get(\\\"receipt_no\\\", \\\"\\\")'''\n\nnew2 = '''        item_id = req.get(\\\"item_id\\\")\n        quantity = req.get(\\\"quantity\\\", 0)\n        unit_cost = req.get(\\\"unit_cost\\\", 0)\n        source = req.get(\\\"source\\\", \\\"\\\")\n        receipt_no = req.get(\\\"receipt_no\\\", \\\"\\\")\n        payment_method = req.get(\\\"payment_method\\\", \\\"\\\")\n        paid_by = req.get(\\\"paid_by\\\", \\\"\\\")\n        staff_name = req.get(\\\"staff_name\\\", \\\"\\\")'''\n\ncontent = content.replace(old2, new2)\n\n# Fix 3: Update INSERT statement to include payment fields\nold3 = '''            \\\"\\\"\\\"INSERT INTO stock_in (batch_id, item_name, quantity, unit_cost, source, receipt_no)\n               VALUES (%s, %s, %s, %s, %s, %s)\\\"\\\"\\\",\n            (batch_id, item[\\\"item_name\\\"], quantity, unit_cost, source, receipt_no)'''\n\nnew3 = '''            \\\"\\\"\\\"INSERT INTO stock_in (batch_id, item_name, quantity, unit_cost, source, receipt_no, payment_method, paid_by, staff_name)\n               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)\\\"\\\"\\\",\n            (batch_id, item[\\\"item_name\\\"], quantity, unit_cost, source, receipt_no, payment_method, paid_by, staff_name)'''\n\ncontent = content.replace(old3, new3)\n\n# Fix 4: Update response to include payment fields\nold4 = '''            \\\"data\\\": {\n                \\\"batch_id\\\": batch_id,\n                \\\"item_name\\\": item[\\\"item_name\\\"],\n                \\\"quantity_added\\\": quantity,\n                \\\"new_quantity\\\": new_qty,\n                \\\"unit_cost\\\": unit_cost,\n            }'''\n\nnew4 = '''            \\\"data\\\": {\n                \\\"batch_id\\\": batch_id,\n                \\\"item_name\\\": item[\\\"item_name\\\"],\n                \\\"quantity_added\\\": quantity,\n                \\\"new_quantity\\\": new_qty,\n                \\\"unit_cost\\\": unit_cost,\n                \\\"payment_method\\\": payment_method,\n                \\\"paid_by\\\": paid_by,\n                \\\"staff_name\\\": staff_name,\n            }'''\n\ncontent = content.replace(old4, new4)\n\nwith open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:\n    f.write(content)\n\nprint('OK - dashboard_routes.py updated')\n\"", (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); process.exit(1); }
    let out = '', serr = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => serr += d.toString());
    stream.on('close', code => {
      console.log('STDOUT:', out);
      if (serr) console.log('STDERR:', serr);
      conn.end();
      process.exit(code || 0);
    });
  });
}).on('error', e => { console.error(e); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 10000 });
