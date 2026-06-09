const {Client} = require("ssh2");
const fs = require("fs");
const conn = new Client();

conn.on("ready", () => {
  const msg = `⚠️ *Construction Bot Access Update*

Three Brothers Construction Bot (@three_brothers_accounting_bot) ၏ access ကို READ-ONLY သို့ ပြောင်းလဲလိုက်ပါပြီ။

🔒 *READ-ONLY MODE*
✅ Allowed: status, logs, files, read, env
❌ Blocked: start, stop, restart, rebuild

📦 *Backup:*
/root/backups/construction_bot_20260529_075042.tar.gz

🔐 *Write Access ပြန်ရဖို့အတွက်:*
Kora လိုမျိုး တိကျသေချာတဲ့ Developer SOP + Code Quality Tools + Knowledge Base တို့ကို အရင်ပြင်ဆင်ရန် လိုအပ်ပါသည်။

1️⃣ Developer SOP (FIX_AGENT_SOP.md, DEV_TEAM_SOP.md, MULTI_PASS_PROTOCOL.md)
2️⃣ Code Quality Tools (import_scanner, integration_tester, fix_safety)
3️⃣ Knowledge Base (CODEBASE_CONTEXT.md, KNOWN_BUG_PATTERNS.md)

ဤအချက်များ ပြည်စုံမှသာ write access ပြန်ပေးမည်။

♻️ *Restore:* tar xzf /root/backups/construction_bot_20260529_075042.tar.gz -C /opt/

🤖 Kora`;

  // URL encode the message
  const encoded = encodeURIComponent(msg);
  
  conn.exec(`curl -s -X POST "https://api.telegram.org/bot8480321890:AAFV5cXPKRF2mAEZ4K86Lf-jd3I5t6PEixQ/sendMessage" -d chat_id=8483598021 -d text="${encoded}" -d parse_mode=Markdown --connect-timeout 10 2>&1`, (err, stream) => {
    let d = "";
    stream.on("data", (c) => d += c);
    stream.on("close", () => { console.log(d); conn.end(); });
  });
});

conn.connect({host:"5.223.81.16", username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")});
