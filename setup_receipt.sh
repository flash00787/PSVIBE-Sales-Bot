#!/bin/bash
# PS VIBE V2 — Receipt Domain Setup
# Run on VPS as root

set -e

BOT_DIR="/root/Sales-Tele-Bot_refactored"
RECEIPTS_DIR="$BOT_DIR/bot/receipts"
API_DIR="$BOT_DIR/api_server"

echo "=== Step 1: Create directories ==="
mkdir -p "$RECEIPTS_DIR" "$API_DIR" "$BOT_DIR/receipts"
echo "Directories created ✅"

echo ""
echo "=== Step 2: Create HTML receipt template ==="

cat > "$BOT_DIR/receipts/template.html" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PS VIBE - Receipt</title>
<style>
  :root {
    --primary: #6C27FF; --primary-dark: #4A0EBD; --accent: #FF2D95;
    --bg: #0D0D1A; --card-bg: #1A1A2E; --card-border: #2D2D4A;
    --text: #E8E8F0; --text-muted: #8888AA; --success: #00E676;
    --warning: #FFD600; --danger: #FF1744;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
  .container { max-width: 480px; width: 100%; padding: 16px; }
  .header { text-align: center; padding: 24px 0 16px; border-bottom: 2px solid var(--primary); margin-bottom: 20px; }
  .header h1 { font-size: 28px; font-weight: 800; background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: 2px; }
  .header .subtitle { font-size: 12px; color: var(--text-muted); margin-top: 4px; letter-spacing: 3px; text-transform: uppercase; }
  .header .badge-receipt { display: inline-block; background: var(--primary); color: white; font-size: 10px; font-weight: 700; padding: 3px 12px; border-radius: 20px; margin-top: 8px; letter-spacing: 1px; text-transform: uppercase; }
  .voucher-banner { background: linear-gradient(135deg, var(--primary-dark), #7C4DFF); border-radius: 12px; padding: 12px 16px; text-align: center; margin-bottom: 16px; }
  .voucher-banner .label { font-size: 10px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.8; }
  .voucher-banner .voucher-id { font-size: 20px; font-weight: 800; letter-spacing: 1px; margin-top: 2px; }
  .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
  .info-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 10px 12px; }
  .info-card .label { font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 3px; }
  .info-card .value { font-size: 14px; font-weight: 600; }
  .section { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; margin-bottom: 12px; overflow: hidden; }
  .section-header { padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--primary); border-bottom: 1px solid var(--card-border); }
  .section-body { padding: 8px 14px; }
  .section-body table { width: 100%; border-collapse: collapse; }
  .section-body th { text-align: left; font-size: 10px; text-transform: uppercase; color: var(--text-muted); padding: 4px 0; letter-spacing: 0.5px; border-bottom: 1px solid var(--card-border); }
  .section-body td { padding: 6px 0; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.04); }
  .section-body td:last-child, .section-body th:last-child { text-align: right; }
  .total-row { display: flex; justify-content: space-between; padding: 6px 14px; font-size: 14px; }
  .total-row.muted { color: var(--text-muted); font-size: 12px; }
  .total-row.grand-total { font-size: 18px; font-weight: 800; padding: 12px 14px; background: linear-gradient(135deg, rgba(108,39,255,0.15), rgba(255,45,149,0.10)); border-top: 2px solid var(--primary); }
  .total-row .amount { font-weight: 700; }
  .total-row .amount.positive { color: var(--success); }
  .total-row .amount.negative { color: var(--danger); }
  .payment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 10px 14px; }
  .payment-item { text-align: center; padding: 8px; border-radius: 8px; background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); }
  .payment-item .pay-label { font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); }
  .payment-item .pay-amount { font-size: 18px; font-weight: 800; }
  .payment-item .pay-amount.cash { color: var(--success); }
  .payment-item .pay-amount.kpay { color: var(--accent); }
  .footer { text-align: center; padding: 24px 0; margin-top: 8px; border-top: 1px solid var(--card-border); }
  .footer .tagline { font-size: 14px; font-weight: 600; background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .footer .copyright { font-size: 10px; color: var(--text-muted); margin-top: 8px; }
  .footer .print-btn { display: inline-block; margin-top: 16px; padding: 10px 32px; border-radius: 25px; border: none; background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; font-size: 14px; font-weight: 700; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
  .footer .print-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(108,39,255,0.4); }
  .footer .print-btn:active { transform: translateY(0); }
  .foc-badge { display: inline-block; background: var(--accent); color: white; font-size: 9px; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-left: 4px; vertical-align: middle; }
  .wallet-display { text-align: center; padding: 10px; background: rgba(0,230,118,0.06); border-radius: 8px; margin: 4px 0; }
  .wallet-display .wallet-label { font-size: 9px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; }
  .wallet-display .wallet-value { font-size: 22px; font-weight: 800; color: var(--success); }
  @media print { body { background: white; color: black; } .header h1, .footer .tagline { -webkit-text-fill-color: initial; background: none; color: var(--primary); } .voucher-banner { background: var(--primary-dark); -webkit-print-color-adjust: exact; print-color-adjust: exact; } .info-card, .section { border-color: #ddd; background: #fafafa; } .total-row.grand-total { background: #f0f0f0; } .footer .print-btn { display: none; } .container { max-width: 100%; padding: 0; } }
</style>
</head>
<body>
<div class="container" id="app">
  <div class="header"><h1>PS VIBE</h1><div class="subtitle">⚡ Gaming Lounge ⚡</div><div class="badge-receipt">🧾 Receipt</div></div>
  <div class="voucher-banner"><div class="label">Voucher ID</div><div class="voucher-id" id="voucherId"></div></div>
  <div class="info-grid">
    <div class="info-card"><div class="label">📅 Date</div><div class="value" id="receiptDate"></div></div>
    <div class="info-card"><div class="label">🕹️ Console</div><div class="value" id="consoleId"></div></div>
    <div class="info-card"><div class="label">👤 Member</div><div class="value" id="memberId"></div></div>
    <div class="info-card"><div class="label">⏱️ Duration</div><div class="value" id="playDuration"></div></div>
  </div>
  <div class="section" id="gameFeeSection">
    <div class="section-header">🎮 Gaming Fee</div>
    <div class="section-body"><table><tr><th>Description</th><th>Amount</th></tr><tr id="gameFeeRow"><td></td><td></td></tr></table></div>
  </div>
  <div class="section" id="foodSection" style="display:none">
    <div class="section-header">🍕 Food & Drinks</div>
    <div class="section-body"><table><tr><th>Item</th><th>Amount</th></tr></table></div>
  </div>
  <div class="section" id="discountSection" style="display:none">
    <div class="section-header">🎁 Discounts & Promotions</div>
    <div id="discountBody"></div>
  </div>
  <div class="section" style="border-color: var(--primary);">
    <div class="total-row muted"><span class="label">Gross Total</span><span class="amount" id="grossTotal"></span></div>
    <div class="total-row muted" id="discountRow" style="display:none"><span class="label">Discount</span><span class="amount negative" id="discountAmount"></span></div>
    <div class="total-row muted" id="bonusRow" style="display:none"><span class="label">🎁 Bonus Minutes</span><span class="amount positive" id="bonusAmount"></span></div>
    <div class="total-row grand-total"><span class="label">💰 Net Total</span><span class="amount" id="netTotal"></span></div>
  </div>
  <div class="section">
    <div class="section-header">💳 Payment</div>
    <div class="payment-grid">
      <div class="payment-item"><div class="pay-label">Cash</div><div class="pay-amount cash" id="cashAmount">0 Ks</div></div>
      <div class="payment-item"><div class="pay-label">KPay</div><div class="pay-amount kpay" id="kpayAmount">0 Ks</div></div>
    </div>
  </div>
  <div class="section" id="walletSection" style="display:none">
    <div class="section-header">💳 Wallet Balance</div>
    <div class="wallet-display">
      <div class="wallet-label">Remaining Balance</div>
      <div class="wallet-value" id="balanceAfter"></div>
      <div style="font-size:11px;color:var(--text-muted);margin-top:4px">Previous: <span id="prevBalance"></span> mins <span id="balanceChange"></span></div>
    </div>
  </div>
  <div class="footer">
    <div class="tagline">🎮 Play The Game. Share The VIBE! 🎮</div>
    <div class="copyright">PS VIBE Gaming Lounge &mdash; Yangon, Myanmar</div>
    <button class="print-btn" onclick="window.print()">🖨️ Print</button>
  </div>
</div>
<script>
(function(){
  var data = window.__RECEIPT_DATA__;
  if(!data){document.getElementById('voucherId').textContent='Receipt not found';return;}
  document.getElementById('voucherId').textContent = data.voucher_id||'-';
  document.getElementById('receiptDate').textContent = data.date||'-';
  document.getElementById('consoleId').textContent = data.console_id||'-';
  document.getElementById('memberId').textContent = data.is_guest ? '👤 Guest' : (data.member_id||'👤 Guest');
  var mins = data.play_mins||0;
  document.getElementById('playDuration').textContent = mins+' mins';
  document.getElementById('gameFeeRow').innerHTML = '<td>🎮 '+mins+' mins'+(data.is_guest?' × '+(data.multiplier||1)+'x':' played')+'</td><td>'+fmtKs(data.game_amt)+'</td>';
  var fi = data.food_items||[];
  if(fi.length>0){
    document.getElementById('foodSection').style.display='block';
    var ft = document.querySelector('#foodSection table');
    fi.forEach(function(it){var r=ft.insertRow();r.innerHTML='<td>'+(it.name||'Item')+' ×'+(it.qty||1)+'</td><td>'+fmtKs(it.subtotal||0)+'</td>';});
  }
  var disc = data.discount||0, promoT = data.promo_title||'', focN = data.foc_item_name||'', focQ = data.foc_item_qty||0, bonus = data.bonus_mins||0;
  if(disc>0||bonus>0||focN){
    document.getElementById('discountSection').style.display='block';
    var db = document.getElementById('discountBody'), lines=[];
    if(focN)lines.push('<div class="section-body"><span class="foc-badge">FOC</span> <strong>'+focN+'</strong> <span style="color:var(--text-muted)">×'+focQ+'</span></div>');
    if(promoT)lines.push('<div style="padding:4px 14px;font-size:12px;color:var(--text-muted)">Promotion: '+promoT+'</div>');
    if(data.promo_note)lines.push('<div style="padding:4px 14px 10px;font-size:11px;color:var(--text-muted)">'+data.promo_note+'</div>');
    db.innerHTML = lines.join('');
  }
  document.getElementById('grossTotal').textContent = fmtKs(data.gross_total||0);
  if(disc>0){document.getElementById('discountRow').style.display='flex';document.getElementById('discountAmount').textContent='-'+fmtKs(disc);}
  if(bonus>0){document.getElementById('bonusRow').style.display='flex';document.getElementById('bonusAmount').textContent='+'+bonus+' mins';}
  document.getElementById('netTotal').textContent = fmtKs(data.net_total||0);
  document.getElementById('cashAmount').textContent = fmtKs(data.cash||0);
  document.getElementById('kpayAmount').textContent = fmtKs(data.kpay||0);
  if(!data.is_guest && data.balance_after!==null && data.balance_after!==undefined){
    document.getElementById('walletSection').style.display='block';
    document.getElementById('balanceAfter').textContent = data.balance_after+' mins';
    document.getElementById('prevBalance').textContent = data.prev_balance||0;
    if(data.balance_change!==null && data.balance_change!==0){
      document.getElementById('balanceChange').textContent = '('+(data.balance_change>0?'+':'')+data.balance_change+' mins)';
    }
  }
  function fmtKs(a){a=a??0;return Number(a).toLocaleString()+' Ks';}
})();
</script>
</body>
</html>
HTMLEOF
echo "HTML template created ✅"

echo ""
echo "=== Step 3: Create receipt handler ==="

cat > "$API_DIR/__init__.py" << 'PYEOF'
"""PS VIBE V2 API Server package."""
__version__ = "2.0.0"
PYEOF

cat > "$API_DIR/receipt_handler.py" << 'PYEOF'
"""
Receipt handler plugin for PS VIBE V2 API Server.
Obfuscated path mapping: z2a3b4 -> "receipt"

Routes:
  GET  /api/z2a3b4/{voucher_id}     -> HTML receipt page
  POST /api/z2a3b4                   -> Receive receipt JSON
  GET  /api/z2a3b4/{voucher_id}/json -> Raw receipt JSON
  GET  /api/z2a3b4                   -> List all receipts
"""
import os
import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)

BOT_DIR = Path(__file__).resolve().parent.parent
RECEIPTS_DIR = BOT_DIR / "bot" / "receipts"
TEMPLATE_PATHS = [
    BOT_DIR / "receipts" / "template.html",
    BOT_DIR / "bot" / "receipts" / "template.html",
]

RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

RECEIPT_SECRET = os.environ.get("RECEIPT_SECRET", "")
RECEIPT_DOMAIN = os.environ.get("RECEIPT_DOMAIN", "")

router = APIRouter(prefix="/api/z2a3b4", tags=["receipt"])

_TEMPLATE_CACHE = None

def _load_template():
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None:
        for p in TEMPLATE_PATHS:
            if p.exists():
                _TEMPLATE_CACHE = p.read_text(encoding="utf-8")
                logger.info("Loaded template from %s", p)
                break
        if _TEMPLATE_CACHE is None:
            logger.warning("Template not found")
            _TEMPLATE_CACHE = "<html><body><h1>Template not found</h1></body></html>"
    return _TEMPLATE_CACHE


@router.get("/{voucher_id}")
async def serve_receipt(voucher_id: str, request: Request):
    safe_id = voucher_id.replace("/", "-").replace("\\", "-")
    json_path = RECEIPTS_DIR / f"{safe_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Receipt not found")
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Read error: {e}")
    html = _load_template()
    html = html.replace("</head>", f"<script>window.__RECEIPT_DATA__ = {json.dumps(data, ensure_ascii=False)};</script></head>", 1)
    return HTMLResponse(content=html)


@router.post("")
async def receive_receipt(request: Request, x_receipt_secret: str = Header(None, alias="x-receipt-secret")):
    if RECEIPT_SECRET and x_receipt_secret != RECEIPT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid receipt secret")
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    voucher_id = data.get("voucher_id", "")
    if not voucher_id:
        raise HTTPException(status_code=400, detail="Missing voucher_id")
    safe_id = voucher_id.replace("/", "-").replace("\\", "-")
    json_path = RECEIPTS_DIR / f"{safe_id}.json"
    try:
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Receipt saved: %s", safe_id)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {e}")
    receipt_url = f"{RECEIPT_DOMAIN}/api/z2a3b4/{safe_id}" if RECEIPT_DOMAIN else ""
    return JSONResponse(content={"status": "ok", "voucher_id": voucher_id, "receipt_url": receipt_url}, status_code=201)


@router.get("/{voucher_id}/json")
async def serve_receipt_json(voucher_id: str):
    safe_id = voucher_id.replace("/", "-").replace("\\", "-")
    json_path = RECEIPTS_DIR / f"{safe_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Receipt not found")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return JSONResponse(content=data)


@router.get("")
async def list_receipts():
    if not RECEIPTS_DIR.exists():
        return {"receipts": [], "count": 0}
    files = sorted(RECEIPTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"receipts": [f.stem for f in files[:100]], "count": len(files)}
PYEOF
echo "Receipt handler created ✅"

echo ""
echo "=== Step 4: Create FastAPI main.py ==="

cat > "$API_DIR/main.py" << 'PYEOF'
"""
PS VIBE V2 FastAPI Server
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("/tmp/psvibe_api_server.log", encoding="utf-8")],
)
logger = logging.getLogger("psvibe_api")

try:
    from api_server.receipt_handler import router as receipt_router
    HAS_RECEIPT = True
    logger.info("Receipt handler loaded (path: /api/z2a3b4)")
except ImportError as e:
    HAS_RECEIPT = False
    logger.warning("Receipt handler not available: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PS VIBE V2 API Server starting on port 8000")
    if os.environ.get("RECEIPT_DOMAIN"):
        logger.info("RECEIPT_DOMAIN: %s", os.environ["RECEIPT_DOMAIN"])
    if os.environ.get("RECEIPT_SECRET"):
        logger.info("RECEIPT_SECRET: configured (%d chars)", len(os.environ["RECEIPT_SECRET"]))
    yield
    logger.info("PS VIBE V2 API Server shutting down")


app = FastAPI(title="PS VIBE V2 API", version="2.0.0", lifespan=lifespan)

if HAS_RECEIPT:
    app.include_router(receipt_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0", "receipt_handler": HAS_RECEIPT}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
PYEOF
echo "FastAPI main.py created ✅"

echo ""
echo "=== Step 5: Set up environment variables ==="
RECEIPT_SECRET=$(tr -dc 'a-zA-Z0-9!@#$%^&*()_+' < /dev/urandom | head -c 32 2>/dev/null || echo "psvibe_receipt_secret_2026_v2")

for var in "RECEIPT_DOMAIN=https://receipt.psvibe.com" "RECEIPT_SECRET=$RECEIPT_SECRET"; do
    key="${var%%=*}"
    if ! grep -q "^$key=" "$BOT_DIR/.env" 2>/dev/null; then
        echo "$var" >> "$BOT_DIR/.env"
        echo "Added $key to .env"
    else
        echo "$key already in .env"
    fi
done

for var in "RECEIPT_DOMAIN=https://receipt.psvibe.com" "RECEIPT_SECRET=$RECEIPT_SECRET"; do
    key="${var%%=*}"
    if ! grep -q "^$key=" /etc/environment 2>/dev/null; then
        echo "$var" >> /etc/environment
    fi
done
echo "Environment updated ✅"
echo "RECEIPT_SECRET=$RECEIPT_SECRET"

echo ""
echo "=== Step 6: Install Python deps ==="
pip3 install fastapi uvicorn python-multipart 2>&1 | tail -2

echo ""
echo "=== Step 7: Create test receipt ==="
cat > "$RECEIPTS_DIR/test-voucher.json" << 'TESTEOF'
{
  "type": "sale",
  "voucher_id": "V-999",
  "date": "5/27/2026",
  "member_id": "PSV_A_042",
  "console_id": "C - 05",
  "play_mins": 120,
  "game_amt": 6000,
  "food_items": [
    {"name": "Pepsi", "qty": 2, "unit_price": 1500, "subtotal": 3000},
    {"name": "Popcorn", "qty": 1, "unit_price": 2000, "subtotal": 2000}
  ],
  "food_total": 5000,
  "gross_total": 11000,
  "discount": 1000,
  "promo_id": "PROMO-001",
  "promo_title": "Weekend Special",
  "promo_note": "1000 Ks off for weekend sessions",
  "foc_item_name": "French Fries",
  "foc_item_qty": 1,
  "bonus_mins": 15,
  "net_total": 10000,
  "kpay": 10000,
  "cash": 0,
  "multiplier": 1.0,
  "is_guest": false,
  "prev_balance": 240,
  "balance_change": -120,
  "balance_after": 135,
  "foc_item_price": 0
}
TESTEOF
echo "Test receipt created ✅"

echo ""
echo "=== Step 8: Install Caddy ==="
if ! command -v caddy &>/dev/null; then
    echo "Installing Caddy..."
    apt-get install -y debian-keyring debian-archive-keyring apt-transport-https 2>/dev/null || true
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null || true
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null 2>&1 || true
    apt-get update -qq 2>/dev/null && apt-get install -y caddy 2>&1 | tail -3
    echo "Caddy installed ✅"
else
    echo "Caddy already: $(caddy version)"
fi

cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak 2>/dev/null || true

cat > /etc/caddy/Caddyfile << 'CADDYEOF'
receipt.psvibe.com {
    reverse_proxy localhost:8000
    header {
        X-Served-By "PS-VIBE-V2"
        -Server
    }
    header /api/z2a3b4/* {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
    }
    log {
        output file /var/log/caddy/receipt.log
        format json
    }
}

ps-vibe.com {
    handle /api/* {
        reverse_proxy localhost:8000
    }
    root * /var/www/ps-vibe
    file_server
    log {
        output file /var/log/caddy/psvibe.log
        format json
    }
}
CADDYEOF

mkdir -p /var/log/caddy /var/www/ps-vibe
systemctl reload caddy 2>/dev/null || systemctl restart caddy 2>/dev/null || echo "Caddy restart attempted"
echo "Caddy configured ✅"

echo ""
echo "=== Step 9: Start API server ==="
cd "$BOT_DIR"
pkill -f "uvicorn.*api_server" 2>/dev/null || true
sleep 1

# Source the .env so the API server gets the env vars
export $(grep -v '^#' "$BOT_DIR/.env" | xargs) 2>/dev/null || true

nohup python3 -m uvicorn api_server.main:app --host 0.0.0.0 --port 8000 > /tmp/api_server.log 2>&1 &
PID=$!
sleep 3

if kill -0 $PID 2>/dev/null; then
    echo "API server running ✅ (PID: $PID)"
else
    echo "API server failed. Logs:"
    cat /tmp/api_server.log
fi

echo ""
echo "=== Step 10: Test ==="
echo "--- Health check:"
curl -s http://localhost:8000/api/health
echo ""
echo "--- Receipt HTML test:"
curl -s -o /dev/null -w "HTTP %{http_code} (%{size_download} bytes)" http://localhost:8000/api/z2a3b4/test-voucher
echo ""
echo "--- Receipt JSON test:"
curl -s http://localhost:8000/api/z2a3b4/test-voucher/json | head -3
echo ""
echo "--- Receipt list:"
curl -s http://localhost:8000/api/z2a3b4

echo ""
echo "=== ALL STEPS COMPLETE ==="
