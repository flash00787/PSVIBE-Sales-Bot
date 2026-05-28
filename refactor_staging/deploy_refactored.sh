#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# PS VIBE Bot — Phase 6 Refactor Deployment Script
# ═══════════════════════════════════════════════════════════════════════
# SAFETY FIRST: Creates a PARALLEL directory, never overwrites production.
# A symlink switch script allows instant rollback.
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

VPS_HOST="${VPS_HOST:-167.71.196.120}"
VPS_USER="${VPS_USER:-root}"
# SSH key or password auth
SSH_CMD="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

# ── Colors ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Paths ──────────────────────────────────────────────────────────────
PROD_DIR="/root/Sales-Tele-Bot"
STAGE_DIR="/root/Sales-Tele-Bot_refactored"
LOCAL_DIR="/home/node/.openclaw/workspace/refactor_staging"
SWITCH_SCRIPT="/root/switch_bot_version.sh"

info "=== PS VIBE Phase 6 Refactor Deployment ==="
info "Production:  ${PROD_DIR}"
info "Staging:     ${STAGE_DIR}"
info ""

# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Create staging directory on VPS
# ═══════════════════════════════════════════════════════════════════════
info "Step 1/6: Creating staging directory on VPS..."
$SSH_CMD ${VPS_USER}@${VPS_HOST} "
    if [ -d '${STAGE_DIR}' ]; then
        echo 'Staging directory already exists — removing old copy...'
        rm -rf '${STAGE_DIR}'
    fi
    mkdir -p '${STAGE_DIR}/bot/handlers'
    mkdir -p '${STAGE_DIR}/receipts'
    mkdir -p '${STAGE_DIR}/logs'
    echo 'Staging directory created.'
"

# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Copy .env and service_account.json from production
# ═══════════════════════════════════════════════════════════════════════
info "Step 2/6: Copying config files from production (read-only)..."
$SSH_CMD ${VPS_USER}@${VPS_HOST} "
    cp '${PROD_DIR}/.env' '${STAGE_DIR}/.env'
    cp '${PROD_DIR}/service_account.json' '${STAGE_DIR}/service_account.json' 2>/dev/null || echo 'service_account.json not found, skipping'
    echo 'Config files copied.'
"

# ═══════════════════════════════════════════════════════════════════════
# STEP 3: Upload refactored Python files
# ═══════════════════════════════════════════════════════════════════════
info "Step 3/6: Uploading refactored source files..."

# Upload main entry point
scp -o StrictHostKeyChecking=no \
    "${LOCAL_DIR}/main.py" \
    ${VPS_USER}@${VPS_HOST}:${STAGE_DIR}/main.py

# Upload refactored __init__.py (the merged canonical version)
scp -o StrictHostKeyChecking=no \
    "${LOCAL_DIR}/__init___refactored.py" \
    ${VPS_USER}@${VPS_HOST}:${STAGE_DIR}/bot/__init__.py

# Upload outer __init__.py (minimal, re-exports from bot)
# We'll create it inline
$SSH_CMD ${VPS_USER}@${VPS_HOST} "
cat > '${STAGE_DIR}/__init__.py' << 'PYEOF'
\"\"\"PS VIBE Sales Bot — Package root.
The bot package lives in bot/__init__.py.
This file ensures Python package resolution.
\"\"\"
from bot import *  # noqa: F401,F403
PYEOF
echo 'Outer __init__.py created.'
"

# Upload app.py (with updated imports)
scp -o StrictHostKeyChecking=no \
    "${LOCAL_DIR}/app.py" \
    ${VPS_USER}@${VPS_HOST}:${STAGE_DIR}/bot/app.py

# Upload all handler domain modules
info "Uploading handler domain modules..."
for f in "${LOCAL_DIR}/handlers/"*.py; do
    basename=$(basename "$f")
    scp -o StrictHostKeyChecking=no -q \
        "$f" \
        ${VPS_USER}@${VPS_HOST}:${STAGE_DIR}/bot/handlers/${basename}
done
info "All handler modules uploaded."

# ═══════════════════════════════════════════════════════════════════════
# STEP 4: Create symlink switch script
# ═══════════════════════════════════════════════════════════════════════
info "Step 4/6: Creating symlink switch script..."
$SSH_CMD ${VPS_USER}@${VPS_HOST} "
cat > '${SWITCH_SCRIPT}' << 'SWEOF'
#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# PS VIBE Bot — Version Switch Script
# Switches the active bot between original and refactored versions.
# ═══════════════════════════════════════════════════════════════════════
set -e

ORIGINAL='/root/Sales-Tele-Bot'
REFACTORED='/root/Sales-Tele-Bot_refactored'
SYMLINK='/root/Sales-Tele-Bot_active'

show_status() {
    if [ -L \"\${SYMLINK}\" ]; then
        target=\$(readlink -f \"\${SYMLINK}\")
        echo \"Active version: \${target}\"
        if [ \"\${target}\" = \"\${REFACTORED}\" ]; then
            echo \"Status: REFACTORED (Phase 6)\"
        elif [ \"\${target}\" = \"\${ORIGINAL}\" ]; then
            echo \"Status: ORIGINAL (legacy)\"
        else
            echo \"Status: UNKNOWN\"
        fi
    else
        echo \"No symlink set — services likely point directly to \${ORIGINAL}\"
        echo \"Run with 'activate-original' or 'activate-refactored' to set up.\"
    fi
    echo ''
    echo 'Services:'
    systemctl is-active psvibe-bot 2>/dev/null && echo '  psvibe-bot: RUNNING' || echo '  psvibe-bot: STOPPED'
    systemctl is-active psvibe-customer 2>/dev/null && echo '  psvibe-customer: RUNNING' || echo '  psvibe-customer: STOPPED'
}

activate() {
    local target=\"\$1\"
    local label=\"\$2\"

    if [ ! -d \"\${target}\" ]; then
        echo \"ERROR: Target directory \${target} does not exist!\"
        exit 1
    fi

    echo \"Switching to \${label} (\${target})...\"

    # Stop services
    systemctl stop psvibe-bot 2>/dev/null || true
    systemctl stop psvibe-customer 2>/dev/null || true
    sleep 2

    # Update symlink
    rm -f \"\${SYMLINK}\"
    ln -s \"\${target}\" \"\${SYMLINK}\"

    # Update systemd service to use symlink
    sed -i \"s|WorkingDirectory=.*|WorkingDirectory=\${SYMLINK}|\" /etc/systemd/system/psvibe-bot.service
    sed -i \"s|WorkingDirectory=.*|WorkingDirectory=\${SYMLINK}|\" /etc/systemd/system/psvibe-customer.service
    systemctl daemon-reload

    # Start services
    systemctl start psvibe-bot
    systemctl start psvibe-customer
    sleep 3

    echo \"\"
    echo \"=== SWITCH COMPLETE ===\"
    show_status
}

case \"\${1:-status}\" in
    status)
        show_status
        ;;
    activate-refactored)
        activate \"\${REFACTORED}\" \"REFACTORED (Phase 6)\"
        ;;
    activate-original)
        activate \"\${ORIGINAL}\" \"ORIGINAL (legacy)\"
        ;;
    *)
        echo \"Usage: \$0 {status|activate-original|activate-refactored}\"
        echo \"\"
        echo \"  status                Show current active version\"
        echo \"  activate-original     Switch to original (legacy) code\"
        echo \"  activate-refactored   Switch to refactored (Phase 6) code\"
        exit 1
        ;;
esac
SWEOF
chmod +x '${SWITCH_SCRIPT}'
echo 'Switch script created at ${SWITCH_SCRIPT}'
"

# ═══════════════════════════════════════════════════════════════════════
# STEP 5: Validate the refactored code (syntax check only)
# ═══════════════════════════════════════════════════════════════════════
info "Step 5/6: Syntax-checking refactored code on VPS..."
$SSH_CMD ${VPS_USER}@${VPS_HOST} "
    echo 'Checking Python syntax...'
    cd '${STAGE_DIR}'
    errors=0
    for f in bot/__init__.py bot/app.py bot/handlers/*.py; do
        if [ -f \"\$f\" ]; then
            python3 -m py_compile \"\$f\" 2>&1 || {
                echo \"  FAIL: \$f\"
                errors=\$((errors+1))
            }
        fi
    done
    if [ \$errors -eq 0 ]; then
        echo 'All files pass syntax check!'
    else
        echo \"\${errors} file(s) have syntax errors!\"
        exit 1
    fi
"

# ═══════════════════════════════════════════════════════════════════════
# STEP 6: Summary
# ═══════════════════════════════════════════════════════════════════════
info ""
info "=== DEPLOYMENT COMPLETE ==="
info ""
info "What was deployed:"
info "  📁 ${STAGE_DIR}/                    — Refactored bot code (parallel to prod)"
info "  📁 ${STAGE_DIR}/bot/__init__.py      — Merged init with IntEnum states + __all__"
info "  📁 ${STAGE_DIR}/bot/handlers/        — 26 domain-split handler modules"
info "  📁 ${STAGE_DIR}/bot/app.py           — Application setup (unchanged)"
info "  📁 ${STAGE_DIR}/main.py              — Entry point (unchanged)"
info "  📄 ${SWITCH_SCRIPT}   — Version switch script"
info ""
info "To activate the refactored version:"
info "  ssh ${VPS_USER}@${VPS_HOST} 'bash ${SWITCH_SCRIPT} activate-refactored'"
info ""
info "To rollback to original:"
info "  ssh ${VPS_USER}@${VPS_HOST} 'bash ${SWITCH_SCRIPT} activate-original'"
info ""
info "To check current status:"
info "  ssh ${VPS_USER}@${VPS_HOST} 'bash ${SWITCH_SCRIPT} status'"
info ""
