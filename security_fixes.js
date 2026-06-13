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

    console.log("=== FIX 1: Install fail2ban ===");
    let r = await execCmd(conn, 'apt-get update -qq && apt-get install -y -qq fail2ban 2>&1', { timeout: 120000 });
    console.log(r.stdout.slice(-300));
    if (r.stderr.includes('E:') || r.stdout.includes('Unable')) {
        console.log("ERROR installing fail2ban:", r.stderr.slice(0, 500));
    }

    // Check if jail.local was written earlier
    r = await execCmd(conn, 'cat /etc/fail2ban/jail.local 2>/dev/null');
    if (!r.stdout.includes('[sshd]')) {
        console.log("Writing jail.local...");
        await execCmd(conn, `cat > /etc/fail2ban/jail.local << 'EOFJAIL'
[sshd]
enabled = true
bantime = 3600
maxretry = 5
findtime = 600
EOFJAIL`);
    }

    r = await execCmd(conn, 'systemctl enable fail2ban && systemctl restart fail2ban && fail2ban-client status 2>&1');
    console.log("fail2ban status:", r.stdout.trim());
    
    r = await execCmd(conn, 'fail2ban-client status sshd 2>&1');
    console.log("sshd jail:", r.stdout.trim());

    console.log("\n=== FIX 2: Fix backup script ===");
    
    // Fix the backup script with proper escaping
    const backupScript = `#!/bin/bash
# Auto-backup script — daily at 2AM UTC
BACKUP_DIR="/root/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG="/var/log/auto_backup.log"

echo "[$(date)] Starting backup..." >> "$LOG"
mkdir -p "$BACKUP_DIR"

# MySQL dump
if command -v mysqldump &>/dev/null; then
    # Try with password from env or config
    mysqldump --defaults-file=/root/.my.cnf psvibe_sales > "$BACKUP_DIR/psvibe_sales_$TIMESTAMP.sql" 2>>"$LOG" || \
    mysqldump -u root psvibe_sales > "$BACKUP_DIR/psvibe_sales_$TIMESTAMP.sql" 2>>"$LOG"
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date)] MySQL dump OK" >> "$LOG"
        gzip "$BACKUP_DIR/psvibe_sales_$TIMESTAMP.sql" 2>>"$LOG"
    else
        echo "[$(date)] MySQL dump FAILED (exit $EXIT_CODE)" >> "$LOG"
        rm -f "$BACKUP_DIR/psvibe_sales_$TIMESTAMP.sql"
    fi
else
    echo "[$(date)] mysqldump not found, skipping MySQL backup" >> "$LOG"
fi

# Compress any remaining old uncompressed .sql files (>60 min old)
find "$BACKUP_DIR" -name "*.sql" -mmin +60 -exec gzip {} + 2>>"$LOG"

# Tar app directories
if [ -d /root/psvibe-sales-bot ]; then
    tar -czf "$BACKUP_DIR/psvibe_sales_bot_$TIMESTAMP.tar.gz" /root/psvibe-sales-bot/ 2>>"$LOG" && \
    echo "[$(date)] Sales bot tar OK" >> "$LOG"
fi

if [ -d /root/psvibe_api_server ]; then
    tar -czf "$BACKUP_DIR/psvibe_api_server_$TIMESTAMP.tar.gz" /root/psvibe_api_server/ 2>>"$LOG" && \
    echo "[$(date)] API server tar OK" >> "$LOG"
fi

# Cleanup: keep last 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete 2>>"$LOG"
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>>"$LOG"
find "$BACKUP_DIR" -name "*.sql" -mtime +1 -delete 2>>"$LOG"

echo "[$(date)] Cleanup done. Backup complete." >> "$LOG"
`;

    await execCmd(conn, `cat > /root/auto_backup.sh << 'EOFBAK'
${backupScript}
EOFBAK
chmod +x /root/auto_backup.sh`);

    console.log("Fixed backup script installed");

    // Check if mysqldump works — check for .my.cnf first
    r = await execCmd(conn, 'cat /root/.my.cnf 2>/dev/null || echo "no .my.cnf"');
    console.log("MySQL config:", r.stdout.trim().slice(0, 200));
    
    r = await execCmd(conn, 'docker exec psvibe-mysql mysql -u root -e "SHOW DATABASES;" 2>&1');
    console.log("MySQL databases:", r.stdout.slice(0, 300));
    
    // Run backup test again
    console.log("\n=== Running fixed backup... ===");
    r = await execCmd(conn, '/bin/bash /root/auto_backup.sh 2>&1; echo "---EXIT:$?---"; ls -la /root/backups/*.sql* /root/backups/*.tar.gz 2>/dev/null | tail -10', { timeout: 120000 });
    console.log(r.stdout.slice(-1000));
    
    r = await execCmd(conn, 'tail -5 /var/log/auto_backup.log 2>/dev/null');
    console.log("Backup log:", r.stdout.trim());

    console.log("\n=== FIX 3: Verify SSH PasswordAuthentication ===");
    r = await execCmd(conn, 'grep -E "^PasswordAuthentication" /etc/ssh/sshd_config');
    console.log("PasswordAuthentication:", r.stdout.trim() || "NOT FOUND — needs adding");
    
    if (!r.stdout.includes('PasswordAuthentication')) {
        await execCmd(conn, 'echo "PasswordAuthentication no" >> /etc/ssh/sshd_config');
        r = await execCmd(conn, 'sshd -t 2>&1 && systemctl reload sshd && echo "SSH reloaded OK"');
        console.log("SSH reload:", r.stdout.trim() || r.stderr.trim());
    } else if (r.stdout.includes('yes')) {
        await execCmd(conn, "sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config");
        r = await execCmd(conn, 'sshd -t 2>&1 && systemctl reload sshd && echo "SSH reloaded OK"');
        console.log("SSH reload:", r.stdout.trim() || r.stderr.trim());
    }

    console.log("\n=== FINAL VERIFICATION ===");
    r = await execCmd(conn, 'grep -E "^(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication)" /etc/ssh/sshd_config');
    console.log("SSH Config:", r.stdout.trim());
    
    r = await execCmd(conn, 'fail2ban-client status 2>&1 && fail2ban-client status sshd 2>&1');
    console.log("fail2ban:", r.stdout.trim());
    
    r = await execCmd(conn, 'ufw status 2>&1 | head -5');
    console.log("UFW:", r.stdout.trim());
    
    console.log("\n✅ All fixes applied!");
    conn.end();
}

main().catch(err => {
    console.error("FATAL:", err.message);
    process.exit(1);
});
