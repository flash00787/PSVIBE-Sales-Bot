echo "=== VPS OpenClaw gateway ==="
systemctl list-units --type=service --all 2>/dev/null | grep openclaw || echo "No openclaw service found"
echo "==="
ps aux | grep "/root/.openclaw\|openclaw" | grep -v grep | grep -v docker | head -10
echo "==="
echo "=== /root/.openclaw sessions ==="
ls /root/.openclaw/agents/main/sessions/ 2>/dev/null | tail -5
echo "==="
echo "=== Nova in contacts? ==="
grep -i "nova" /root/.openclaw/workspace/*.md 2>/dev/null | head -5
