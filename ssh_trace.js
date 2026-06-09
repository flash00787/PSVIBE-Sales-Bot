const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

const commands = [
  // Flow 1: Booking trace
  `echo "=== FLOW 1: BOOKING TRACE ==="`,
  `echo "--- booking.py + booking_flow.py ---"`,
  `grep -n "BOOK\\|SBK\\|BTN_BOOK\\|BOOK_CONSOLE\\|BOOK_MEMBER\\|CB_" /root/psvibe-sale-bot/bot/handlers/booking.py /root/psvibe-sale-bot/bot/handlers/booking_flow.py 2>/dev/null | head -40`,
  `echo "--- Console_Booking in __init__.py ---"`,
  `grep -n "Console_Booking\\|BOOKING" /root/psvibe-sale-bot/bot/__init__.py | head -10`,

  // Flow 2: Console Management trace
  `echo ""`,
  `echo "=== FLOW 2: CONSOLE MANAGEMENT TRACE ==="`,
  `echo "--- console_mgmt.py etc in __init__.py ---"`,
  `grep -n "CON_MGMT\\|CON_ADD\\|CON_DEL\\|GAME_ADD\\|GAME_DEL\\|GINST_\\|SSD_" /root/psvibe-sale-bot/bot/__init__.py | head -30`,
  `echo "--- console_mgmt.py ---"`,
  `grep -n "console\\|CONSOLE\\|STATUS\\|console_status\\|Console_Status" /root/psvibe-sale-bot/bot/handlers/console_mgmt.py 2>/dev/null | head -20`,
  `echo "--- games.py ---"`,
  `grep -n "GAME\\|GINST\\|INSTALL\\|game_lib\\|install" /root/psvibe-sale-bot/bot/handlers/games.py 2>/dev/null | head -20`,

  // Flow 3: Stock trace
  `echo ""`,
  `echo "=== FLOW 3: STOCK TRACE ==="`,
  `echo "--- STOCK in __init__.py ---"`,
  `grep -n "STOCK_\\|SI_\\|INVENTORY\\|Stock_In\\|Stock_Out" /root/psvibe-sale-bot/bot/__init__.py | head -20`,
  `echo "--- stock.py + stock_in.py ---"`,
  `grep -n "STOCK_IN\\|STOCK_OUT\\|inventory" /root/psvibe-sale-bot/bot/handlers/stock.py /root/psvibe-sale-bot/bot/handlers/stock_in.py 2>/dev/null | head -20`,

  // Additional deep trace
  `echo ""`,
  `echo "=== DEEP TRACE: booking_flow.py ==="`,
  `grep -n "BOOK_LINK\\|BOOK_CONSOLE\\|BOOK_MEMBER\\|BOOK_DATE\\|BOOK_TIME\\|BOOK_GAME\\|BOOK_CONFIRM\\|SBK" /root/psvibe-sale-bot/bot/handlers/booking_flow.py 2>/dev/null | head -30`,

  `echo ""`,
  `echo "=== DEEP TRACE: console.py ==="`,
  `grep -n "console\\|CONSOLE\\|STATUS\\|status\\|Console_Booking\\|Console_Status\\|COB_" /root/psvibe-sale-bot/bot/handlers/console.py 2>/dev/null | head -30`,

  `echo ""`,
  `echo "=== DEEP TRACE: ginst.py ==="`,
  `grep -n "GINST\\|install\\|SSD\\|HHD\\|transfer" /root/psvibe-sale-bot/bot/handlers/ginst.py 2>/dev/null | head -20`,

  `echo ""`,
  `echo "=== DEEP TRACE: ssd_disc.py ==="`,
  `grep -n "SSD\\|HHD\\|transfer\\|MOVE\\|disc" /root/psvibe-sale-bot/bot/handlers/ssd_disc.py 2>/dev/null | head -20`,

  `echo ""`,
  `echo "=== DEEP TRACE: stock.py full state machine ==="`,
  `grep -n "STOCK_IN\\|STOCK_OUT\\|INVENTORY\\|SI_\\|def \\|class " /root/psvibe-sale-bot/bot/handlers/stock.py 2>/dev/null | head -40`,
  
  `echo ""`,
  `echo "=== DEEP TRACE: stock_in.py full state machine ==="`,
  `grep -n "STOCK\\|SI_\\|SO_\\|def \\|class \\|INVENTORY" /root/psvibe-sale-bot/bot/handlers/stock_in.py 2>/dev/null | head -40`,

  // API/google sheets trace
  `echo ""`,
  `echo "=== API/SHEETS TRACE: booking ==="`,
  `grep -n "create_booking\\|Console_Booking\\|Console_Status\\|Setting\\|append_row\\|update_row\\|get_sheet" /root/psvibe-sale-bot/bot/handlers/booking_flow.py 2>/dev/null | head -20`,

  `echo ""`,
  `echo "=== API/SHEETS TRACE: console mgmt ==="`,
  `grep -n "append_row\\|update_row\\|get_sheet\\|Console_Status\\|Console_List\\|Game_Lib" /root/psvibe-sale-bot/bot/handlers/console_mgmt.py /root/psvibe-sale-bot/bot/handlers/games.py 2>/dev/null | head -20`,

  `echo ""`,
  `echo "=== API/SHEETS TRACE: stock ==="`,
  `grep -n "append_row\\|update_row\\|get_sheet\\|Stock_In\\|Stock_Out\\|Inventory" /root/psvibe-sale-bot/bot/handlers/stock.py /root/psvibe-sale-bot/bot/handlers/stock_in.py 2>/dev/null | head -20`,
];

conn.on('ready', () => {
  conn.exec(commands.join(' && '), (err, stream) => {
    if (err) throw err;
    let output = '';
    stream.on('close', (code) => {
      console.log('Exit code:', code);
      // Write output to file
      fs.writeFileSync('/home/node/.openclaw/workspace/audit/raw_trace.txt', output);
      console.log('=== OUTPUT ===');
      console.log(output);
      conn.end();
    }).on('data', (data) => {
      output += data.toString();
    }).stderr.on('data', (data) => {
      output += 'STDERR: ' + data.toString();
    });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 10000,
});
