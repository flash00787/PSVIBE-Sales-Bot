echo "=== Nova gateway 상태 ==="
# Check if port 18790 is in use
ss -tlnp 2>/dev/null | grep 18790
echo "---"
# Check openclaw config
cat /root/.openclaw/openclaw.json 2>/dev/null | python3 -c "
import json,sys
c=json.load(sys.stdin)
g=c.get('gateway',{})
print('Gateway mode:', g.get('mode'))
print('Gateway bind:', g.get('bind'))
print('Gateway port:', g.get('port'))
channels = c.get('channels',{})
for ch,v in channels.items():
    if isinstance(v, dict):
        print(f'Channel {ch}: enabled={v.get(\"enabled\")}, token_present={\"token\" in str(v.get(\"botToken\",\"\"))}')
" 2>/dev/null
echo "==="
echo "=== Starting Nova ==="
# Try to start as the right user
# Check if we need to use su or runuser
cd /root/.openclaw && OPENCLAW_CONFIG_PATH=/root/.openclaw/openclaw.json nohup /usr/bin/openclaw gateway start --port 18790 > /tmp/nova-gateway.log 2>&1 &
NOVA_PID=$!
echo "Nova PID: $NOVA_PID"
sleep 4
echo "---"
# Check if it's running
ps aux | grep "openclaw gateway" | grep -v grep | head -3
echo "---"
curl -s --connect-timeout 3 http://localhost:18790/health 2>&1
