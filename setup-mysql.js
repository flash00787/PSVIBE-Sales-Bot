const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const VPS_HOST = '5.223.81.16';
const VPS_USER = 'root';
const VPS_PASS = 'S1_PSVIBE_2024';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

function runCmd(client, cmd) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '';
      let stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => {
        resolve({ stdout: stdout.trim(), stderr: stderr.trim(), code });
      });
    });
  });
}

async function main() {
  console.log('=== Connecting to VPS... ===');
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({
      host: VPS_HOST,
      port: 22,
      username: VPS_USER,
      // password: VPS_PASS,
      privateKey: fs.readFileSync(KEY_PATH, 'utf8'),
      keepaliveInterval: 10000,
      readyTimeout: 30000,
    });
  });
  console.log('=== Connected to VPS ===\n');

  // Step 2: Check Docker
  console.log('--- Checking Docker availability ---');
  let r = await runCmd(conn, 'which docker && docker --version');
  if (r.code === 0) {
    console.log('Docker found:', r.stdout);
  } else {
    console.log('Docker not found. Installing Docker...');
    // Install Docker using convenience script
    r = await runCmd(conn, 'curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh');
    if (r.code !== 0) {
      console.error('Docker install failed:', r.stderr);
      process.exit(1);
    }
    console.log('Docker installed successfully.');
    r = await runCmd(conn, 'docker --version');
    console.log(r.stdout);
  }

  // Step 3: Pull MySQL 8.0 image and run container
  console.log('\n--- Pulling MySQL 8.0 image ---');
  r = await runCmd(conn, 'docker pull mysql:8.0');
  console.log(r.stdout.slice(-200));
  if (r.stderr) console.log('Stderr:', r.stderr.slice(-200));

  console.log('\n--- Stopping/removing old container if exists ---');
  await runCmd(conn, 'docker rm -f psvibe-mysql 2>/dev/null; true');

  console.log('\n--- Running MySQL container ---');
  const runCmdStr = `docker run -d \
    --name psvibe-mysql \
    --restart unless-stopped \
    -p 3306:3306 \
    -e MYSQL_ROOT_PASSWORD=PsVibe@MySQL2024! \
    -e MYSQL_DATABASE=psvibe_api \
    -e MYSQL_USER=psvibe_user \
    -e MYSQL_PASSWORD=PsVibe@User2024! \
    -v psvibe_mysql_data:/var/lib/mysql \
    mysql:8.0`;
  
  r = await runCmd(conn, runCmdStr);
  console.log('Container create result:', r.stdout);
  if (r.stderr) console.log('Stderr:', r.stderr);

  // Wait for MySQL to be ready
  console.log('\n--- Waiting for MySQL to be ready (up to 60s) ---');
  let ready = false;
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 1000));
    r = await runCmd(conn, "docker exec psvibe-mysql mysql -uroot -p'PsVibe@MySQL2024!' -e 'SELECT 1' 2>/dev/null");
    if (r.code === 0) {
      ready = true;
      console.log('MySQL is ready after', i + 1, 'seconds');
      break;
    }
  }
  if (!ready) {
    console.error('MySQL failed to start in 60s');
    r = await runCmd(conn, 'docker logs psvibe-mysql --tail 20');
    console.error('Container logs:', r.stdout);
    process.exit(1);
  }

  // Step 4: Verify container
  console.log('\n--- Verifying container ---');
  r = await runCmd(conn, 'docker ps --filter name=psvibe-mysql --format "{{.ID}} {{.Status}} {{.Ports}}"');
  console.log(r.stdout);
  if (r.code !== 0 || !r.stdout.includes('Up')) {
    console.error('Container not running properly');
    process.exit(1);
  }

  // Step 5: Test connection with psvibe_user
  console.log('\n--- Testing connection ---');
  r = await runCmd(conn, "docker exec psvibe-mysql mysql -u psvibe_user -p'PsVibe@User2024!' psvibe_api -e 'SELECT 1 AS test;'");
  console.log('Test query result:');
  console.log(r.stdout);
  if (r.code !== 0) console.error('Test failed:', r.stderr);

  // Step 6: Create tables
  console.log('\n--- Creating tables ---');
  const tablesSql = `
CREATE TABLE IF NOT EXISTS sync_status (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sheet_name VARCHAR(100) NOT NULL,
  last_sync_at DATETIME NOT NULL,
  rows_synced INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_sheet (sheet_name)
);

CREATE TABLE IF NOT EXISTS member_wallets (
  member_id VARCHAR(50) PRIMARY KEY,
  balance_mins INT DEFAULT 0,
  member_name VARCHAR(200),
  phone VARCHAR(50),
  effective_rate DECIMAL(10,2) DEFAULT 1.0,
  tier VARCHAR(50),
  total_spend DECIMAL(15,2) DEFAULT 0,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS console_status (
  console_id VARCHAR(20) PRIMARY KEY,
  status VARCHAR(50),
  current_game TEXT,
  current_member VARCHAR(100),
  start_time DATETIME,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staff_records (
  staff_id INT AUTO_INCREMENT PRIMARY KEY,
  staff_name VARCHAR(200) NOT NULL,
  base_salary DECIMAL(12,2) DEFAULT 0,
  role VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS games_library (
  game_title VARCHAR(200) PRIMARY KEY,
  genre VARCHAR(100),
  disc_count INT DEFAULT 0,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
`;
  r = await runCmd(conn, `docker exec -i psvibe-mysql mysql -u root -p'PsVibe@MySQL2024!' psvibe_api <<'SQLEOF'
${tablesSql}
SQLEOF`);
  console.log('Table creation result:', r.stdout);
  if (r.stderr) console.log('Stderr:', r.stderr);

  // Step 7: Verify tables
  console.log('\n--- Verifying tables ---');
  r = await runCmd(conn, "docker exec psvibe-mysql mysql -u root -p'PsVibe@MySQL2024!' psvibe_api -e 'SHOW TABLES;'");
  console.log('Tables in psvibe_api:');
  console.log(r.stdout);

  // Step 8: Write completion status
  console.log('\n--- Writing completion status ---');
  r = await runCmd(conn, 'mkdir -p /root/agent_output');
  r = await runCmd(conn, `cat > /root/agent_output/DB_SETUP_DONE.txt <<'EOF'
MySQL Docker Setup Complete
===========================
Date: ${new Date().toISOString()}
Host: ${VPS_HOST}

Status: SUCCESS

Container: psvibe-mysql (MySQL 8.0)
Port: 3306
Data Volume: psvibe_mysql_data

Database: psvibe_api
Root Password: [stored in container env]
App User: psvibe_user
App Password: [stored in container env]

Tables Created:
- sync_status (sync tracking)
- member_wallets (member balances)
- console_status (console tracking)
- staff_records (staff management)
- games_library (game catalog)
EOF`);
  console.log('Status file written.');

  // Final summary
  console.log('\n========================================');
  console.log('✅ MySQL Docker Setup Complete!');
  console.log('========================================');
  console.log('Container: psvibe-mysql');
  console.log('Database: psvibe_api');
  console.log('User: psvibe_user');
  console.log('Tables: sync_status, member_wallets, console_status, staff_records, games_library');
  console.log('========================================');

  conn.end();
}

main().catch(err => {
  console.error('Fatal error:', err);
  conn.end();
  process.exit(1);
});
