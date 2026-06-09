const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const checks = [];
  
  // 1. Check SQLite database
  checks.push(() => {
    c.exec("echo '=== SQLite DB CHECK ===' && sqlite3 /root/Sales-Tele-Bot_refactored/psvibe.db 'SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name;' 2>&1 || echo 'No DB file found'", (e, s) => {
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(o); next(); });
    });
  });
  
  // 2. Check bot_status.log for API errors  
  checks.push(() => {
    c.exec("echo '=== BOT_STATUS.LOG ERRORS ===' && grep -i 'error\\|fail\\|timeout\\|traceback\\|exception\\|401\\|403\\|500\\|429' /root/Sales-Tele-Bot_refactored/bot_status.log 2>/dev/null | tail -20 || echo 'No status log'", (e, s) => {
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(o); next(); });
    });
  });
  
  // 3. Check bot.log for API errors
  checks.push(() => {
    c.exec("echo '=== BOT.LOG API ERRORS ===' && grep -i 'error\\|fail\\|timeout\\|traceback\\|exception\\|401\\|403\\|500\\|429' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null | tail -20 || echo 'No errors found'", (e, s) => {
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(o); next(); });
    });
  });
  
  // 4. Check Sheets API connection
  checks.push(() => {
    c.exec("echo '=== SHEETS API CHECK ===' && grep 'gspread\\|sheet\\|spreadsheet\\|worksheet\\|API' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null | tail -20", (e, s) => {
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(o); next(); });
    });
  });
  
  // 5. Check Telegram API connection health
  checks.push(() => {
    c.exec("echo '=== TG API HEALTH ===' && grep 'getMe\\|getUpdates\\|HTTP Request.*200 OK' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null | tail -10", (e, s) => {
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(o); next(); });
    });
  });
  
  // 6. DB sync check (SQLite -> Sheets)
  checks.push(() => {
    c.exec("echo '=== DB SYNC STATUS ===' && if [ -f /root/Sales-Tele-Bot_refactored/sqlite/sync.log ]; then tail -10 /root/Sales-Tele-Bot_refactored/sqlite/sync.log; else echo 'No sync log found'; fi", (e, s) => {
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(o); next(); });
    });
  });
  
  // 7. Check config cache
  checks.push(() => {
    c.exec("echo '=== CONFIG CACHE ===' && grep 'cache\\|refresh\\|fetch' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null | tail -10", (e, s) => {
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(o); next(); });
    });
  });
  
  let idx = 0;
  function next() {
    idx++;
    if (idx < checks.length) {
      checks[idx]();
    } else {
      c.end();
    }
  }
  checks[0]();
  
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
