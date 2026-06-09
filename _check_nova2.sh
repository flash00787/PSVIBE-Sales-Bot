echo "=== OpenClaw agents on VPS ==="
cat /root/.openclaw/openclaw.json 2>/dev/null | python3 -c "
import json,sys
c=json.load(sys.stdin)
agents = c.get('agents', {})
print('Agents:')
for k,v in agents.items():
    if isinstance(v, dict):
        m = v.get('model', v.get('primary', 'N/A'))
        print(f'  {k}: model={m}')
    else:
        print(f'  {k}: {v}')
" 2>/dev/null || echo "Failed to parse"

echo "==="
echo "=== Agent configs ==="
ls -la /root/.openclaw/agents/ 2>/dev/null
echo "---"
for d in /root/.openclaw/agents/*/; do
    echo "Agent: $(basename $d)"
    ls "$d" 2>/dev/null | head -5
    echo ""
done 2>/dev/null
