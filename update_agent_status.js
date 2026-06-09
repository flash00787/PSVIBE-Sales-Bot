const {Client} = require('ssh2');
const fs = require('fs');
const newEntry = `

## Agent: Architect (Kora) — 2026-05-27 14:15 UTC

**Task:** payment-breakdown-system-design
**Status:** PASS
**Notes:** Designed payment breakdown system supporting 5 methods. Doc saved to payment_design.md.
**Files changed:** payment_design.md (VPS), TASK_payment_design.md (VPS)
`;
const c = new Client();
c.on('ready', () => {
  const b64 = Buffer.from(newEntry).toString('base64');
  c.exec(`echo ${b64} | base64 -d >> "/root/Aung Chan Myint/.coordination/AGENT_STATUS.md" && echo UPDATED`, (e, s) => {
    let o = '';
    s.on('data', d => o += d);
    s.stderr.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host:'5.223.81.16', username:'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')});
