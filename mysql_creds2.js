const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync(path.join(__dirname, '.ssh', 'id_rsa'));

function execCmd(conn, cmd, options = {}) {
    return new Promise((resolve, reject) => {
        const timeout = options.timeout || 30000;
        conn.exec(cmd, (err, stream) => {
            if (err) return reject(err);
            let stdout = '', stderr = '';
            stream.on('data', d => stdout += d.toString());
            stream.stderr.on('data', d => stderr += d.toString());
            const timer = setTimeout(() => {
                stream.close();
                resolve({ stdout: stdout + '\n[TIMEOUT]', stderr });
            }, timeout);
            stream.on('close', (code) => {
                clearTimeout(timer);
                resolve({ stdout, stderr, code });
            });
        });
    });
}

async function main() {
    const conn = new Client();
    
    await new Promise((resolve, reject) => {
        conn.on('ready', resolve);
        conn.on('error', reject);
        conn.connect({ host: HOST, username: USER, privateKey: KEY });
    });

    // Check all docker compose files
    console.log("=== Checking all compose files ===");
    let r = await execCmd(conn, 'find / -maxdepth 5 -name "docker-compose*.yml" -o -name "docker-compose*.yaml" 2>/dev/null | head -20');
    console.log("Compose files found:", r.stdout.trim());
    
    r = await execCmd(conn, 'find / -maxdepth 4 -name "compose*.yml" -o -name "compose*.yaml" 2>/dev/null | head -10');
    console.log("More:", r.stdout.trim());

    // Check docker inspect for compose project
    r = await execCmd(conn, 'docker inspect psvibe-mysql --format "{{json .Config.Labels}}" 2>/dev/null');
    console.log("\n=== MySQL Labels ===");
    console.log(r.stdout.slice(0, 1000));

    // Find the compose file for this container
    r = await execCmd(conn, 'docker inspect psvibe-mysql --format "{{.Config.Labels}}" 2>/dev/null | grep -o "com.docker.compose.project.working_dir:[^ ]*"');
    console.log("\nWorking dir:", r.stdout.trim());

    r = await execCmd(conn, 'docker inspect psvibe-mysql --format "{{range .Config.Env}}{{println .}}{{end}}" 2>/dev/null');
    console.log("\n=== ALL MySQL container env ===");
    console.log(r.stdout.slice(0, 1000));

    // Check in common locations
    r = await execCmd(conn, 'ls -la /root/docker-compose* /opt/*/docker-compose* /srv/*/docker-compose* 2>/dev/null');
    console.log("\n=== Compose files ===");
    console.log(r.stdout.trim());

    // Check if there's a pw in MySQL container directly
    r = await execCmd(conn, 'docker exec psvibe-mysql printenv 2>/dev/null | sort');
    console.log("\n=== MySQL container env ===");
    console.log(r.stdout.trim());

    // The mysql container might use MYSQL_ROOT_PASSWORD
    r = await execCmd(conn, 'docker inspect psvibe-mysql 2>/dev/null | grep -i "ROOT\|PASS\|MYSQL" | head -10');
    console.log("\n=== MySQL inspect grep ===");
    console.log(r.stdout.trim());

    conn.end();
}

main().catch(err => console.error("FATAL:", err.message));
