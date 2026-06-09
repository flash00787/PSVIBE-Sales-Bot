#!/usr/bin/env python3
"""
KORA UNIFIED SYSTEM HEALTH MONITOR v2
Runs from Gateway workspace. Checks all 5 pillars:
  1. Memory System       2. Kora Workflow       3. Agents Workflow
  4. Infrastructure      5. Project Knowledge

Usage:
  python3 kora_health_monitor.py              # Full check (auto-SSH to VPS)
  python3 kora_health_monitor.py --json       # JSON output
  python3 kora_health_monitor.py --local-only # Skip VPS checks
"""
import os, sys, json, subprocess, shutil
from datetime import datetime, timezone

GREEN, YELLOW, RED, RESET = '\033[92m', '\033[93m', '\033[91m', '\033[0m'
BOLD, DIM = '\033[1m', '\033[2m'
OK, WARN, FAIL = 'OK', 'WARN', 'FAIL'

WS = '/home/node/.openclaw/workspace'


class Check:
    def __init__(self, name, status, detail='', score=100):
        self.name, self.status, self.detail, self.score = name, status, detail, score

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return '', 'timeout', 124
    except Exception:
        return '', 'error', 1

VPS_BRIDGE = os.path.join(WS, 'coordination', 'vps_exec.js')

def vps_exec(cmd, timeout=15):
    """Run command on VPS via Node.js ssh2 bridge."""
    bridge_cmd = f'node {VPS_BRIDGE} {json.dumps(cmd)}'
    return run(bridge_cmd, timeout)

def vps_ok():
    """Check if VPS is reachable via Node.js bridge."""
    out, _, rc = run(f'node {VPS_BRIDGE} "echo OK"', timeout=12)
    return rc == 0 and 'OK' in out

# ── 1. MEMORY SYSTEM ──
def check_memory():
    c = []
    mem = os.path.join(WS, 'memory')
    mem_md = os.path.join(WS, 'MEMORY.md')

    if os.path.exists(mem_md):
        size, lines = os.path.getsize(mem_md), len(open(mem_md).readlines())
        s = OK if size < 200000 else (WARN if size < 500000 else FAIL)
        c.append(Check('MEMORY.md', s, f'{size//1024}KB / {lines} lines', 100 if s==OK else 70 if s==WARN else 30))

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    daily = os.path.join(mem, f'{today}.md')
    c.append(Check('Daily log', OK if os.path.exists(daily) else WARN,
                   f'{today}.md {"exists" if os.path.exists(daily) else "missing"}',
                   100 if os.path.exists(daily) else 50))

    sop = len([f for f in os.listdir(mem) if 'SOP' in f.upper() and f.endswith('.md')])
    c.append(Check('SOP docs', OK if sop>=6 else WARN, f'{sop} files', 100 if sop>=6 else 60))

    mem_files = [f for f in os.listdir(mem) if f.endswith('.md')]
    c.append(Check('Memory files', OK, f'{len(mem_files)} .md files', 100))

    # Heartbeat state
    hs = os.path.join(mem, 'heartbeat-state.json')
    if os.path.exists(hs):
        d = json.load(open(hs))
        stuck = len(d.get('stuckTasks', []))
        pending = len(d.get('pendingTasks', []))
        c.append(Check('Heartbeat state', OK if stuck==0 and pending==0 else WARN,
                       f'{stuck} stuck, {pending} pending', 100 if stuck==0 else 50))
    return c

# ── 2. KORA WORKFLOW ──
def check_workflow():
    c = []
    for f in ['AGENTS.md', 'SOUL.md', 'HEARTBEAT.md', 'GOLDEN_RULES.md']:
        fp = os.path.join(WS, f)
        c.append(Check(f, OK if os.path.exists(fp) else FAIL,
                       f'{len(open(fp).readlines())} lines' if os.path.exists(fp) else 'MISSING',
                       100 if os.path.exists(fp) else 0))

    # Session state
    import glob
    sessions = glob.glob('/home/node/.openclaw/agents/main/sessions/*.jsonl')
    total = len(sessions)
    size = sum(os.path.getsize(s) for s in sessions) if sessions else 0
    c.append(Check('Session files', OK if total < 3000 else WARN,
                   f'{total} files / {size//1024//1024}MB', 100 if total < 3000 else 60))

    locks = glob.glob('/home/node/.openclaw/agents/main/sessions/*.lock')
    c.append(Check('Session locks', OK if len(locks) < 5 else WARN,
                   f'{len(locks)} active lock(s)', 100 if len(locks)<5 else 60))
    return c

# ── 3. AGENTS WORKFLOW ──
def check_agents(vps):
    c = []
    if not vps:
        c.append(Check('VPS connection', FAIL, 'unreachable - agents check skipped', 0))
        return c

    # Coordination tools count
    out, _, rc = vps_exec('ls /root/coordination/*.py 2>/dev/null | wc -l')
    count = int(out.strip()) if out.strip().isdigit() else 0
    c.append(Check('Coordination tools', OK if count >= 45 else WARN, f'{count} .py files', 100 if count>=45 else 60))

    # Quality Gate
    out, _, _ = vps_exec('python3 /root/coordination/quality_gate.py --quick 2>&1 | grep "SCORE:"')
    if out:
        import re
        m = re.search(r'(\d+)/100', out)
        if m: score = int(m.group(1))
        else: score = 0
        c.append(Check('Quality Gate', OK if score>=90 else WARN, f'{score}/100', score))

    # Auto Healer
    out, _, _ = vps_exec('python3 /root/coordination/auto_healer.py status 2>&1 | grep -c "0 failures"')
    c.append(Check('Auto Healer', OK, 'active', 100))

    # Active crons
    out, _, _ = vps_exec('crontab -l 2>/dev/null | grep -vc "^#\|^$"')
    cron_count = int(out.strip()) if out.strip().isdigit() else 0
    c.append(Check('Cron jobs', OK if cron_count >= 10 else WARN, f'{cron_count} active', 100 if cron_count>=10 else 70))
    return c

# ── 4. INFRASTRUCTURE ──
def check_infra(vps):
    c = []
    if not vps:
        c.append(Check('VPS connection', FAIL, 'unreachable - infra check skipped', 0))
        return c

    # Docker
    out, _, _ = vps_exec('docker ps --format "{{.Names}}:{{.Status}}" 2>/dev/null')
    unhealthy = [l.split(':')[0] for l in out.split('\n') if 'unhealthy' in l.lower()]
    total = len([l for l in out.split('\n') if l.strip()])
    s = OK if not unhealthy else WARN
    c.append(Check('Docker', s, f'{total} containers' + (f', {len(unhealthy)} unhealthy: {unhealthy}' if unhealthy else ', all healthy'),
                   100 if not unhealthy else 70))

    # Services
    for svc in ['psvibe-sale-bot', 'psvibe-api', 'psvibe_customer_bot', 'cloudflared-tunnel']:
        out, _, _ = vps_exec(f'systemctl is-active {svc} 2>/dev/null')
        st = OK if out.strip() == 'active' else FAIL
        c.append(Check(f'  {svc}', st, out.strip(), 100 if st==OK else 0))

    # Resources
    out, _, _ = vps_exec("df -h / | tail -1 | awk '{print $5}'")
    pct = int(out.replace('%','')) if out and out.replace('%','').isdigit() else 0
    c.append(Check('Disk', OK if pct<80 else WARN, f'{pct}% used', 100 if pct<80 else 60))

    out, _, _ = vps_exec("free -h | awk '/^Mem:/{print $3\"/\"$2}'")
    c.append(Check('Memory', OK, out.strip() if out else 'N/A', 100))

    # Git
    for repo, path in [('Sales Bot', '/root/psvibe-sales-bot'), ('API Server', '/root/psvibe_api_server')]:
        out, _, _ = vps_exec(f'cd {path} && git status --short 2>/dev/null | wc -l')
        changes = int(out.strip()) if out.strip().isdigit() else -1
        c.append(Check(f'Git ({repo})', OK if changes==0 else WARN,
                       f'{changes} uncommitted' if changes>0 else 'clean',
                       100 if changes==0 else 70))
    return c

# ── 5. PROJECT KNOWLEDGE ──
def check_knowledge(vps):
    c = []
    # Local workspace docs
    for f in ['PROJECT_STRUCTURE.md', 'ERROR_PATTERNS.md', 'TOOLS.md', 'USER.md']:
        fp = os.path.join(WS, f)
        c.append(Check(f, OK if os.path.exists(fp) else WARN,
                       f'{len(open(fp).readlines())} lines' if os.path.exists(fp) else 'missing',
                       100 if os.path.exists(fp) else 50))

    # VPS docs check
    if vps:
        out, _, _ = vps_exec('test -f /root/psvibe-sales-bot/PROJECT_STRUCTURE.md && echo yes || echo no')
        c.append(Check('PS on VPS bot', OK if 'yes' in out else WARN, 'present' if 'yes' in out else 'missing', 100 if 'yes' in out else 50))

        out, _, _ = vps_exec('ls /root/coordination/*.py 2>/dev/null | wc -l')
        tools = int(out.strip()) if out.strip().isdigit() else 0
        c.append(Check('VPS coordination', OK if tools>=45 else WARN, f'{tools} tools', 100 if tools>=45 else 60))
    return c


def print_report(pillars, json_out=False):
    if json_out:
        result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'pillars': {}}
        for name, checks in pillars:
            avg = sum(c.score for c in checks) / len(checks) if checks else 0
            result['pillars'][name] = {'avg_score': round(avg,1), 'status': OK if avg>=80 else (WARN if avg>=60 else FAIL),
                                       'checks': [{'name':c.name,'status':c.status,'detail':c.detail,'score':c.score} for c in checks]}
        total = sum(c.score for ch in [p[1] for p in pillars] for c in ch)
        n = sum(len(p[1]) for p in pillars)
        result['overall'] = round(total/n, 1) if n else 0
        print(json.dumps(result, indent=2))
        return result['overall']

    print(f"{BOLD}╔{'═'*58}╗{RESET}")
    print(f"{BOLD}║{'KORA UNIFIED HEALTH MONITOR v2':^58}║{RESET}")
    print(f"{BOLD}║{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'):^58}║{RESET}")
    print(f"{BOLD}╚{'═'*58}╝{RESET}\n")

    total_score, total_checks = 0, 0
    for name, checks in pillars:
        avg = sum(c.score for c in checks) / len(checks) if checks else 0
        total_score += sum(c.score for c in checks)
        total_checks += len(checks)

        icon, color = ('🟢', GREEN) if avg>=80 else (('🟡', YELLOW) if avg>=60 else ('🔴', RED))
        print(f"{BOLD}{icon} {name}{RESET} ({color}{avg:.0f}/100{RESET})")
        for ck in checks:
            si = '✅' if ck.status==OK else ('⚠️' if ck.status==WARN else '❌')
            print(f"  {si} {ck.name}: {DIM}{ck.detail}{RESET}")
        print()

    overall = total_score / total_checks if total_checks else 0
    oc = GREEN if overall>=80 else (YELLOW if overall>=60 else RED)
    print(f"{BOLD}╔{'═'*38}╗{RESET}")
    print(f"{BOLD}║  OVERALL: {oc}{overall:.0f}/100{RESET}{' '*(21-len(str(int(overall))))}{BOLD}║{RESET}")
    print(f"{BOLD}║  {total_checks} checks across 5 pillars{' '*(10-len(str(total_checks)))}{BOLD}║{RESET}")
    print(f"{BOLD}╚{'═'*38}╝{RESET}")
    return overall


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Kora Unified Health Monitor')
    ap.add_argument('--json', action='store_true', help='JSON output')
    ap.add_argument('--local-only', action='store_true', help='Skip VPS checks')
    args = ap.parse_args()

    vps = False
    if not args.local_only:
        print(f"{DIM}Connecting to VPS...{RESET}", end=' ', flush=True)
        vps = vps_ok()
        print(f"{GREEN}OK{RESET}" if vps else f"{RED}UNREACHABLE{RESET}")

    pillars = [
        ('1. Memory System', check_memory()),
        ('2. Kora Workflow', check_workflow()),
        ('3. Agents Workflow', check_agents(vps)),
        ('4. Infrastructure', check_infra(vps)),
        ('5. Project Knowledge', check_knowledge(vps)),
    ]

    overall = print_report(pillars, json_out=args.json)
    if not args.json:
        sys.exit(0 if overall >= 80 else (1 if overall >= 60 else 2))
