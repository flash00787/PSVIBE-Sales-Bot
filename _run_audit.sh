#!/bin/bash
# Run full V2 audit via SSH

VPS="5.223.81.16"
KEY="/home/node/.openclaw/workspace/.ssh/id_rsa"
V2="/root/Sales-Tele-Bot_refactored"
V1="/root/staging/monolithic_ref"
OUT="/home/node/.openclaw/workspace"

ssh_cmd() {
  ssh -o StrictHostKeyChecking=no -i "$KEY" "root@$VPS" "$1" 2>&1
}

echo "========================================"
echo "A1: FILE TREE"
echo "========================================"
ssh_cmd "cd $V2 && find . -name '*.py' -not -path '*/__pycache__/*' | sort" > "$OUT/A1_filetree.txt"
echo "Python files: $(wc -l < "$OUT/A1_filetree.txt")"

echo "========================================"
echo "A1: SYNTAX CHECK"
echo "========================================"
ssh_cmd "cd $V2 && python3 << 'PYEOF'
import ast, os
errors = []
for root, dirs, files in os.walk('.'):
    if '__pycache__' in root: continue
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            try:
                with open(fp) as fh:
                    ast.parse(fh.read())
            except SyntaxError as e:
                errors.append(f'{fp}: {e}')
if errors:
    for e in errors: print(e)
else:
    print('ALL FILES PASS SYNTAX CHECK')
PYEOF" > "$OUT/A1_syntax.txt"

echo "========================================"
echo "A1: IMPORT ANALYSIS"
echo "========================================"
ssh_cmd "cd $V2 && grep -rn \"from bot import \\*\" bot/ --include='*.py' | wc -l" > "$OUT/A1_starimport_count.txt"
ssh_cmd "cd $V2 && grep -rn \"from bot import \\*\" bot/ --include='*.py'" > "$OUT/A1_starimport_files.txt"
ssh_cmd "cd $V2 && grep -A5 '__all__' bot/__init__.py | head -20" > "$OUT/A1_all_export.txt"

echo "========================================"
echo "A2: FUNCTION PARITY"
echo "========================================"
ssh_cmd "cd $V1 && grep -n '^def \|^async def ' main.py" > "$OUT/A2_v1_functions.txt"
echo "V1 functions: $(wc -l < "$OUT/A2_v1_functions.txt")"
ssh_cmd "cd $V2 && grep -rn '^def \|^async def ' bot/ --include='*.py'" > "$OUT/A2_v2_functions.txt"
echo "V2 functions: $(wc -l < "$OUT/A2_v2_functions.txt")"

echo "Critical helpers:"
ssh_cmd "cd $V2 && for fn in now_mmt today_str step_hdr calc_duration _sheets_retry fetch_allowed_staff_ids _int _pin_then _replit_get _replit_post _replit_patch _replit_delete _api_base; do echo -n \"\$fn: \"; grep -rn \"def \$fn\" bot/ --include='*.py' | head -1 || echo 'MISSING'; done" > "$OUT/A2_critical_helpers.txt"
cat "$OUT/A2_critical_helpers.txt"

echo "========================================"
echo "A3: STATES AUDIT"
echo "========================================"
ssh_cmd "cd $V2 && grep -n '= auto()' bot/__init__.py 2>/dev/null | head -5" > "$OUT/A3_state_enum.txt"
echo "States: $(wc -l < "$OUT/A3_state_enum.txt")"
ssh_cmd "cd $V2 && grep -n 'entry_points\|states\|fallbacks' bot/app.py | head -20" > "$OUT/A3_app_states.txt"
ssh_cmd "cd $V2 && grep -n 'class BotState' bot/__init__.py 2>/dev/null || echo 'No BotState class'" > "$OUT/A3_botstate_class.txt"

echo "========================================"
echo "A4: DEAD CODE"
echo "========================================"
ssh_cmd "cd $V2 && echo '=== sqlite/ exists? ==='; ls -la sqlite/ 2>&1; echo '=== imported? ==='; grep -rn 'sqlite\|db_manager\|PSVibeDB' bot/ --include='*.py' 2>/dev/null || echo 'NO REFERENCES'" > "$OUT/A4_sqlite.txt"
cat "$OUT/A4_sqlite.txt"

ssh_cmd "cd $V2 && echo '=== bot/bot/ ==='; ls -la bot/bot/ 2>&1; echo '=== handlers/ ==='; ls -la handlers/ 2>&1; echo '=== app.py ==='; ls -la app.py 2>&1; echo '=== keep_alive.py ==='; ls -la keep_alive.py 2>&1" > "$OUT/A4_duplicates.txt"

echo "========================================"
echo "A5: SECURITY"
echo "========================================"
ssh_cmd "cd $V2 && grep -rn 'sk-\|xai-\|sk-or' bot/ --include='*.py' | grep -v 'os.environ\|environ.get\|__all__' | grep -v '^.*#' || echo 'NO HARDCODED SECRETS'" > "$OUT/A5_secrets.txt"
cat "$OUT/A5_secrets.txt"

ssh_cmd "ls -la /etc/systemd/system/psvibe-bot-refactored.service 2>&1" > "$OUT/A5_service_perm.txt"
ssh_cmd "ls -la $V2/.env 2>&1" > "$OUT/A5_env_perm.txt"
ssh_cmd "ps aux | grep python | grep -v grep | head -10" > "$OUT/A5_processes.txt"

echo "========================================"
echo "ALL AUDITS COMPLETE"
echo "========================================"
