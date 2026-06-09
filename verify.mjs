import { Client } from 'ssh2';
import { readFileSync } from 'fs';

const conn = new Client();
const PK = readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function exec(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let out = '', errOut = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => errOut += d.toString());
      stream.on('close', code => {
        if (code !== 0) reject(new Error(`Exit ${code}: ${errOut || out}`));
        else resolve(out);
      });
    });
  });
}

conn.on('ready', async () => {
  try {
    console.log('=== ROUTER ===');
    console.log(await exec(conn, 'head -50 /root/psvibe-dashboard/src/router/index.ts'));
    console.log('\n=== VERIFY VIEWS (ls) ===');
    console.log(await exec(conn, 'ls -la /root/psvibe-dashboard/src/views/BookingsManagement.vue /root/psvibe-dashboard/src/views/MembersManagement.vue /root/psvibe-dashboard/src/views/FoodStock.vue /root/psvibe-dashboard/src/views/Promotions.vue /root/psvibe-dashboard/src/views/GamesLibrary.vue'));
    console.log('\n=== SIDEBAR nav items ===');
    const sidebar = await exec(conn, 'cat /root/psvibe-dashboard/src/views/DashboardView.vue');
    // Extract nav buttons
    const lines = sidebar.split('\n');
    for (const line of lines) {
      if (line.includes('navigateTo(') || line.includes('<span>Dashboard</span>') || line.includes('<span>Bookings</span>') || line.includes('<span>Members</span>') || line.includes('<span>Food') || line.includes('<span>Promo') || line.includes('<span>Games')) {
        console.log(line.trim());
      }
    }
    console.log('\n=== DIST CHECK ===');
    console.log(await exec(conn, 'ls /root/psvibe_api_server/dashboard-dist/assets/ | head'));
    console.log('\n=== API STATUS ===');
    console.log(await exec(conn, 'systemctl is-active psvibe-api'));
    conn.end();
  } catch(e) {
    console.error('FAIL:', e.message);
    conn.end();
  }
});

conn.connect({ host:'5.223.81.16', port:22, username:'root', privateKey:PK, readyTimeout:15000 });
