/**
 * SSH Helper for VPS (5.223.81.16)
 * Shared module for all Kora workspace tools
 */
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const VPS_CONFIG = {
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync(path.join(__dirname, '..', '.ssh', 'id_rsa')),
  readyTimeout: 20000,
};

/**
 * Execute a command on the VPS via SSH
 * @param {string} cmd - Shell command to run
 * @param {number} timeout - Timeout in ms (default 30000)
 * @returns {Promise<string>} stdout + stderr combined
 */
function sshExec(cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let output = '';
    const timer = setTimeout(() => {
      conn.end();
      reject(new Error(`SSH timeout after ${timeout}ms`));
    }, timeout);

    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { clearTimeout(timer); conn.end(); return reject(err); }
        stream.on('data', d => { output += d.toString(); });
        stream.stderr.on('data', d => { output += d.toString(); });
        stream.on('close', () => { clearTimeout(timer); conn.end(); resolve(output); });
      });
    });
    conn.on('error', (e) => { clearTimeout(timer); reject(e); });
    conn.connect(VPS_CONFIG);
  });
}

/**
 * Execute a MySQL query on the VPS Docker container
 * @param {string} query - SQL query
 * @returns {Promise<string>} Tab-separated output
 */
function mysqlQuery(query) {
  const escaped = query.replace(/"/g, '\\"');
  return sshExec(
    `docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" psvibe_api -e "${escaped}" 2>&1`,
    15000
  );
}

/**
 * Check VPS system resources
 */
async function checkSystemResources() {
  const commands = {
    cpu: 'top -bn1 | head -5',
    mem: 'free -m',
    disk: 'df -h /',
    docker: 'docker ps --format "{{.Names}} {{.Status}}"',
    uptime: 'uptime',
  };
  const results = {};
  for (const [key, cmd] of Object.entries(commands)) {
    try { results[key] = await sshExec(cmd, 10000); }
    catch(e) { results[key] = 'ERROR: ' + e.message; }
  }
  return results;
}

module.exports = { sshExec, mysqlQuery, checkSystemResources, VPS_CONFIG };
