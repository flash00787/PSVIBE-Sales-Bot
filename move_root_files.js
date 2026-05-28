#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  // Step 1: kill bots, create target dir
  conn.exec('pkill -f "python3 main.py" 2>/dev/null; pkill -f "python3 customer_bot.py" 2>/dev/null; pkill -f "node api_server.js" 2>/dev/null; sleep 1; mkdir -p "/root/Aung Chan Myint"; echo "STEP1_DONE"', (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log('KILL+DIR:', out.trim());

      // Step 2: move project directories
      const dirs = [
        'Sales-Tele-Bot', 'Sales-Tele-Bot_refactored', 'Sales-Tele-Bot_refactored.bak',
        'Sales-Tele-Bot_refactored.predeploy2', 'Sales-Tele-Bot_refactored.predeploy5', 'Sales-Tele-Bot_staging',
        'Personal-Wallet-Tele-Bot', 'Personal-Wallet-Tele-Bot-2',
        'backups', 'staging', 'monitoring', 'receipts', '.coordination', '.Trash'
      ];
      const moveCmd = 'mv ' + dirs.join(' ') + ' "/root/Aung Chan Myint/" && echo "DIRS_DONE"';
      conn.exec(moveCmd, (e2, s2) => {
        let o2 = '';
        s2.on('data', d => o2 += d.toString());
        s2.stderr.on('data', d => o2 += d.toString());
        s2.on('close', () => {
          console.log('DIRS:', o2.trim());

          // Step 3: move project files
          const files = [
            'Caddyfile', 'docker-compose.yml', 'docker-compose.yml.bak',
            'PRODUCTION', 'bot_status.log', 'customer_bot.log',
            'database_backup.sql', 'deploy_vps.sh', 'health_status.sh',
            'setup_receipt.sh', 'start_bots.sh', 'start_bots2.sh',
            'start_wallet_bot.sh', 'switch_bot_version.sh',
            'psvibe_bots_audit_report.md',
            'new_kora_sa.json', 'service_account.json', 'client_secret.json',
            'gmail_send.py', 'gmail_token.json', 'email_body.txt',
            'get-docker.sh', 'workflows_export.json'
          ];
          const fileCmd = 'mv ' + files.join(' ') + ' "/root/Aung Chan Myint/" && echo "FILES_DONE"';
          conn.exec(fileCmd, (e3, s3) => {
            let o3 = '';
            s3.on('data', d => o3 += d.toString());
            s3.stderr.on('data', d => o3 += d.toString());
            s3.on('close', () => {
              console.log('FILES:', o3.trim());

              // Step 4: clean up random artifact files
              conn.exec('rm -f "=" "=0?:" "0" "=0?Added Mins:Deducted Mins" "=1500" "=1500?bonus1500:0" "=2000" "=2000?bonus2000:play_hrs" "e --version"; echo "CLEAN_DONE"', (e4, s4) => {
                let o4 = '';
                s4.on('data', d => o4 += d.toString());
                s4.stderr.on('data', d => o4 += d.toString());
                s4.on('close', () => {
                  console.log('CLEAN:', o4.trim());

                  // Step 5: create symlinks for Sales-Tele-Bot (so running scripts still work)
                  conn.exec('ln -sf "/root/Aung Chan Myint/Sales-Tele-Bot" /root/Sales-Tele-Bot && echo "SYMLINK_DONE"', (e5, s5) => {
                    let o5 = '';
                    s5.on('data', d => o5 += d.toString());
                    s5.stderr.on('data', d => o5 += d.toString());
                    s5.on('close', () => {
                      console.log('SYMLINK:', o5.trim());

                      // Step 6: final verification
                      conn.exec('echo "=== Final check ==="; ls -la /root/ | grep -v "^total" | head -20; echo "..."; ls -la "/root/Aung Chan Myint/" | head -30', (e6, s6) => {
                        let o6 = '';
                        s6.on('data', d => o6 += d.toString());
                        s6.stderr.on('data', d => o6 += d.toString());
                        s6.on('close', () => {
                          console.log(o6);
                          conn.end();
                        });
                      });
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
});
conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
