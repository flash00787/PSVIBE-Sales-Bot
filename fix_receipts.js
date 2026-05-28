const {Client} = require('ssh2');
const fs = require('fs');
const c = new Client();
c.on('ready', () => {
  const script = `
cd "/root/Aung Chan Myint/Sales-Tele-Bot/api_server"
# Read current api_server.js, replace the 3 receipt payment rows
# The pattern: static KPay+Cash rows → dynamic conditional rows
node -e '
const fs = require("fs");
let js = fs.readFileSync("api_server.js", "utf8");

// Build the replacement: KPay+Cash + conditional Wave/CB/AYA rows
const newRows = \`<tr class="payment-row"><td>KPay</td><td class="right">\${fmt(d.kpay)} Ks</td></tr><tr class="payment-row"><td>Cash</td><td class="right">\${fmt(d.cash)} Ks</td></tr>\${d.wave?\\`<tr class="payment-row"><td>Wave Money</td><td class="right">\${fmt(d.wave)} Ks</td></tr>\\`:""}\${d.cb?\\`<tr class="payment-row"><td>CB Pay</td><td class="right">\${fmt(d.cb)} Ks</td></tr>\\`:""}\${d.aya?\\`<tr class="payment-row"><td>AYA Pay</td><td class="right">\${fmt(d.aya)} Ks</td></tr>\\`:""}\`;

const oldRow = \`<tr class="payment-row"><td>KPay</td><td class="right">\${fmt(d.kpay)} Ks</td></tr><tr class="payment-row"><td>Cash</td><td class="right">\${fmt(d.cash)} Ks</td></tr>\`;

// Replace all 3 occurrences (sale, topup, new_member receipts)
const count = (js.match(new RegExp(oldRow.replace(/[.*+?^\${}()|[\\]\\\\\\\\]/g, "\\\\\\\\$&"), "g")) || []).length;
js = js.split(oldRow).join(newRows);
fs.writeFileSync("api_server.js", js);
console.log("Replaced " + count + " occurrences");
'
echo API_DONE
`;
  const b64 = Buffer.from(script).toString('base64');
  c.exec(`echo ${b64} | base64 -d | bash`, (e, s) => {
    let o = '';
    s.on('data', d => o += d);
    s.stderr.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host:'5.223.81.16', username:'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')});
