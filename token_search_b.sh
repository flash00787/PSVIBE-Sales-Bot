#!/bin/bash
TOKEN="8545665013:AAFgEuw4V_715Q9yzGOYloinIdbdYXYb8zU"
OUTFILE="/root/token_search_b.txt"

echo "========================================" > "$OUTFILE"
echo " Bot Token Search Report (Agent B)" >> "$OUTFILE"
echo " Token: $TOKEN" >> "$OUTFILE"
echo " Date : $(date)" >> "$OUTFILE"
echo "========================================" >> "$OUTFILE"
echo "" >> "$OUTFILE"

# CHECK 1: Running processes
echo "=== CHECK 1: Running processes ===" | tee -a "$OUTFILE"
ps aux | grep -i '8545665013' 2>/dev/null >> "$OUTFILE"
RESULT1=$(ps aux | grep -c '8545665013' 2>/dev/null)
if [ "$RESULT1" -eq 0 ]; then
  echo "[NO MATCH] No running processes contain the token." >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# CHECK 2: Environment variables in running processes
echo "=== CHECK 2: Environment variables in running Python processes ===" | tee -a "$OUTFILE"
PY_PIDS=$(pgrep -f python 2>/dev/null)
if [ -n "$PY_PIDS" ]; then
  for pid in $PY_PIDS; do
    if [ -f "/proc/$pid/environ" ]; then
      RESULT=$(strings /proc/$pid/environ 2>/dev/null | grep -i '8545665013')
      if [ -n "$RESULT" ]; then
        echo "FOUND in PID $pid: $RESULT" >> "$OUTFILE"
      fi
    fi
  done
  echo "[INFO] Checked $PY_PIDS Python PIDs — no token in environ." >> "$OUTFILE"
else
  echo "[INFO] No Python processes running." >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# CHECK 3: Systemd services and psvibe files
echo "=== CHECK 3: Systemd service files ===" | tee -a "$OUTFILE"
SYSD_RESULT=$(grep -rn '8545665013' /etc/systemd/system/ 2>/dev/null)
if [ -n "$SYSD_RESULT" ]; then
  echo "$SYSD_RESULT" >> "$OUTFILE"
else
  echo "[NO MATCH] No token in /etc/systemd/system/" >> "$OUTFILE"
fi

echo "=== CHECK 3b: psvibe config files ===" | tee -a "$OUTFILE"
PSVIBE_RESULT=$(grep -rn '8545665013' /etc/psvibe/ 2>/dev/null)
if [ -n "$PSVIBE_RESULT" ]; then
  echo "$PSVIBE_RESULT" >> "$OUTFILE"
else
  echo "[NO MATCH] No token in /etc/psvibe/" >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# CHECK 4: Cron jobs
echo "=== CHECK 4: Cron jobs ===" | tee -a "$OUTFILE"
CRON_FOUND=0
for f in /var/spool/cron/crontabs/* /etc/crontab /etc/cron.d/*; do
  if [ -f "$f" ]; then
    if grep -l '8545665013' "$f" 2>/dev/null; then
      echo "FOUND in: $f" >> "$OUTFILE"
      CRON_FOUND=1
    fi
  fi
done
if [ "$CRON_FOUND" -eq 0 ]; then
  echo "[NO MATCH] No token in cron files." >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# CHECK 5: .env files
echo "=== CHECK 5: .env files ===" | tee -a "$OUTFILE"
ENV_FOUND=0
while IFS= read -r f; do
  if grep -q '8545665013' "$f" 2>/dev/null; then
    echo "FOUND ENV: $f" >> "$OUTFILE"
    ENV_FOUND=1
  fi
done < <(find /root /etc /home -name ".env" -o -name "*.env" 2>/dev/null)
if [ "$ENV_FOUND" -eq 0 ]; then
  echo "[NO MATCH] No token in .env files found." >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# CHECK 6: Python/json/yaml files
echo "=== CHECK 6: Python/json/yaml/config files under /root ===" | tee -a "$OUTFILE"
FILE_RESULT=$(grep -rl '8545665013' /root --include='*.py' --include='*.json' --include='*.yaml' --include='*.yml' --include='*.toml' --include='*.cfg' --include='*.ini' --include='*.conf' 2>/dev/null)
if [ -n "$FILE_RESULT" ]; then
  echo "$FILE_RESULT" >> "$OUTFILE"
else
  echo "[NO MATCH] No token found in any source/config files under /root." >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

# CHECK 7: Also grep /opt, /var/www, /srv for good measure
echo "=== CHECK 7: Extended search (/opt, /var/www, /srv) ===" | tee -a "$OUTFILE"
EXTRA_RESULT=$(grep -rl '8545665013' /opt /var/www /srv --include='*.py' --include='*.json' --include='*.yaml' --include='*.yml' --include='*.env' --include='*.txt' --include='*.sh' --include='*.conf' --include='*.ini' 2>/dev/null)
if [ -n "$EXTRA_RESULT" ]; then
  echo "$EXTRA_RESULT" >> "$OUTFILE"
else
  echo "[NO MATCH] No token found in /opt, /var/www, or /srv." >> "$OUTFILE"
fi
echo "" >> "$OUTFILE"

echo "========================================" >> "$OUTFILE"
echo "Search complete." >> "$OUTFILE"
cat "$OUTFILE"
