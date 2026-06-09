echo "=== Nova check on VPS ==="
ls -la /root/.openclaw/ 2>/dev/null
echo "==="
ps aux | grep -i "openclaw\|nova" | grep -v grep | head -10
echo "==="
echo "=== Docker ==="
docker ps --format "{{.Names}} {{.Status}}" 2>/dev/null
echo "==="
echo "=== OpenClaw process on VPS ==="
pgrep -af openclaw 2>/dev/null || echo "No openclaw process found"
