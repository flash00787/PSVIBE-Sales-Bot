const { Client } = require('ssh2');
const fs = require('fs');
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const VPS = '5.223.81.16';
const DIR = '/root/Aung Chan Myint/Sales-Tele-Bot';

function ssh(cmd) {
  return new Promise(function(resolve, reject) {
    const conn = new Client();
    let out = '';
    conn.on('ready', function() {
      conn.exec(cmd, function(err, stream) {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', function(d) { out += d.toString(); });
        stream.stderr.on('data', function(d) { out += d.toString(); });
        stream.on('close', function() { conn.end(); resolve(out); });
      });
    }).on('error', function(e) { conn.end(); reject(e); })
    .connect({
      host: VPS, username: 'root',
      privateKey: fs.readFileSync(KEY),
      readyTimeout: 30000
    });
  });
}

async function main() {
  var r;
  
  // Show context around the broken line
  r = await ssh("sed -n '6992,7002p' \"" + DIR + "/main.py\"");
  console.log('BEFORE FIX:');
  console.log(r);
  
  // Read the file, fix line 6996 (0-indexed: 6995), write back
  // Using Python to do in-place fix
  var pyScript = "p='" + DIR + "/main.py';";
  pyScript += "f=open(p);";
  pyScript += "l=f.readlines();";
  pyScript += "f.close();";
  pyScript += "l[6995]='        '+l[6995].lstrip();";
  pyScript += "f=open(p,'w');";
  pyScript += "f.writelines(l);";
  pyScript += "f.close();";
  pyScript += "print('FIXED')";
  
  r = await ssh("python3 -c \"" + pyScript + "\"");
  console.log('Fix result:', r.trim());
  
  // Verify
  r = await ssh("sed -n '6992,7002p' \"" + DIR + "/main.py\"");
  console.log('AFTER FIX:');
  console.log(r);
  
  // Syntax check
  r = await ssh("python3 -c \"import ast; ast.parse(open('" + DIR + "/main.py').read()); print('SYNTAX PASS')\"");
  console.log('Syntax check:', r.trim());
  
  // Also verify bot files
  r = await ssh("python3 -c \"import ast; ast.parse(open('" + DIR + "/bot/__init__.py').read()); print('INIT PASS')\"");
  console.log('bot/__init__.py:', r.trim());
  
  r = await ssh("python3 -c \"import ast; ast.parse(open('" + DIR + "/bot/handlers.py').read()); print('HANDLERS PASS')\"");
  console.log('bot/handlers.py:', r.trim());
  
  r = await ssh("python3 -c \"import ast; ast.parse(open('" + DIR + "/bot/app.py').read()); print('APP PASS')\"");
  console.log('bot/app.py:', r.trim());
  
  r = await ssh("python3 -c \"import ast; ast.parse(open('" + DIR + "/customer_bot.py').read()); print('CUSTOMER PASS')\"");
  console.log('customer_bot.py:', r.trim());
  
  console.log('\n=== ALL FIXES COMPLETE ===');
}

main().catch(function(e) { console.error(e); });
