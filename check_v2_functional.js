const {Client} = require('ssh2');
const c = new Client();
const HOST = '167.71.196.120';
const PASS = 'Freedom2024#RevFlash';

const results = [];

function run(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (e, s) => {
        if (e) { conn.end(); reject(e); return; }
        let o = '';
        s.on('data', d => o += d);
        s.on('close', () => { conn.end(); resolve(o); });
      });
    }).connect({host: HOST, port: 22, username: 'root', password: PASS, readyTimeout: 10000});
  });
}

async function main() {
  const pad = '─'.repeat(60);
  console.log(pad);
  console.log('V.2 — COMPREHENSIVE FUNCTIONAL CHECK');
  console.log(pad);

  // 1. Service
  let out = await run('systemctl is-active psvibe-bot-refactored');
  console.log(`\n📦 Service: ${out.trim()}`);

  // 2. PID + uptime
  out = await run('ps -p $(systemctl show -p MainPID psvibe-bot-refactored 2>/dev/null | cut -d= -f2) -o pid,etimes,args --no-headers 2>/dev/null');
  console.log(`PID/Uptime: ${out.trim() || '(checking...)'}`);

  // 3. Memory
  out = await run("ps aux | grep python3 | grep -v grep | awk '{print $2 \" \" $6/1024 \" MB \" $11}' | head -5");
  console.log('\nMemory:');
  for (const l of out.trim().split('\n')) console.log(`  ${l}`);

  // 4. Log tail
  out = await run('tail -15 /root/Sales-Tele-Bot_refactored/logs/bot.log');
  console.log('\n📋 LOG (last 15):');
  for (const l of out.trim().split('\n')) console.log(`  ${l}`);

  // 5. Error count
  out = await run("grep -ci 'ERROR\\|Traceback\\|NameError\\|KeyError' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null || echo 0");
  console.log(`\n🔴 Error/Traceback count: ${out.trim()}`);

  // 6. Import checks
  console.log('\n🔬 IMPORT CHECKS:');
  const checks = [
    'from bot import main, keep_alive, ensure_sheet_headers',
    'from bot.handlers import *',
    'from bot.handlers.console import *',
    'from bot.handlers.booking import *',
    'from bot.handlers.games import *',
    'from bot.handlers.stock import *',
    'from bot.handlers.main_menu import *',
    'from bot.handlers.sales import *',
  ];
  for (const check of checks) {
    const pyCmd = `cd /root/Sales-Tele-Bot_refactored && python3 -c "${check}; print('OK')" 2>&1`;
    out = await run(pyCmd);
    const ok = out.trim().includes('OK');
    console.log(`  ${ok ? '✅' : '❌'} ${check}${ok ? '' : ' → ' + out.trim().split('\\n').slice(-1)[0].slice(0, 80)}`);
  }

  // 7. Symbol check 
  console.log('\n🎯 SYMBOL CHECK:');
  const symbols = ['show_main_menu', 'prompt_book_console', 'show_game_menu', 'prompt_member', 'cmd_inventory', 'step_console_menu'];
  for (const sym of symbols) {
    const pyCmd = `cd /root/Sales-Tele-Bot_refactored && python3 -c "from bot.handlers import *; print(type(${sym}).__name__)" 2>&1`;
    out = await run(pyCmd);
    const ok = out.trim().includes('function') || out.trim().includes('type') || out.trim().includes('method');
    console.log(`  ${ok ? '✅' : '❌'} ${sym} → ${ok ? 'defined' : out.trim().slice(0, 80)}`);
  }

  console.log(`\n${pad}`);
  console.log('CHECK COMPLETE');
  console.log(pad);
}

main().catch(e => { console.error(e); process.exit(1); });
