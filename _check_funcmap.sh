cat /root/agent_output/function_map.json | python3 -c '
import json,sys
d = json.load(sys.stdin)
keys = list(d.keys())
print("=== KEYS ===", keys)
funcs = d.get("functions", [])
print("=== FUNCTIONS (first 40) ===")
for f in funcs[:40]:
    if isinstance(f, dict):
        n = f.get("name","?")
        fl = f.get("file","")
        t = f.get("type","")
        p = f.get("params","")
        print(f"{n:35s} | {fl:25s} | {t:10s} | {str(p)[:40]}")
    else:
        print(f)
print(f"\nTotal: {len(funcs)} functions")
'
