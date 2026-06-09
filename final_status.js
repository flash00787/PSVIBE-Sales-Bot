const {Client} = require('ssh2');
const fs = require('fs');
const entry = `

## Agent: Coder (Kora) — 2026-05-27 14:30 UTC

**Task:** payment-breakdown-system-implementation
**Status:** PASS
**Notes:** Implemented Payment Breakdown System (Phase 1). Added columns, write ranges, read accumulators, receipt templates, analytics.
**Files changed:**
- main.py: Sales_Daily write (A:R+3zeros), TopUp_Log writes (E:M+3zeros), calc_pnl reads
- api_server.js: 3 receipt templates (dynamic rows), daily summary, monthly report
- Sheets: Sales_Daily P=Wave, Q=CB Pay, R=AYA Pay; TopUp_Log K=Wave, L=CB Pay, M=AYA Pay
`;
const c = new Client();
c.on('ready', () => {
  const b64 = Buffer.from(entry).toString('base64');
  c.exec(`echo ${b64} | base64 -d >> "/root/Aung Chan Myint/.coordination/AGENT_STATUS.md" && echo OK`, (e, s) => {
    let o = '';
    s.on('data', d => o += d);
    s.stderr.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host:'5.223.81.16', username:'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')});
