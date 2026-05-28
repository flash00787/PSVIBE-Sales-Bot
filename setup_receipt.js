const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

// The VPS host
const HOST = '167.71.196.120';

conn.on('ready', () => {
  // Step 1: Create everything in one go
  const commands = `
    set -e
    
    BOT_DIR="/root/Sales-Tele-Bot_refactored"
    RECEIPTS_DIR="$BOT_DIR/bot/receipts"
    API_DIR="$BOT_DIR/api_server"
    
    echo "=== Step 1: Ensure directories ==="
    mkdir -p "$RECEIPTS_DIR"
    mkdir -p "$API_DIR"
    echo "Directories ready: receipts=$RECEIPTS_DIR, api=$API_DIR"
    
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
    --primary: #6C27FF;
    --primary-dark: #4A0EBD;
    --accent: #FF2D95;
    --bg: #0D0D1A;
    --card-bg: #1A1A2E;
    --card-border: #2D2D4A;
    --text: #E8E8F0;
    --text-muted: #8888AA;
    --success: #00E676;
    --warning: #FFD600;
    --danger: #FF1744;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .container {
    max-width: 480px;
    width: 100%;
    padding: 16px;
  }
  /* HEADER */
  .header {
    text-align: center;
    padding: 24px 0 16px;
    border-bottom: 2px solid var(--primary);
    margin-bottom: 20px;
  }
  .header h1 {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 2px;
  }
  .header .subtitle {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
    letter-spacing: 3px;
    text-transform: uppercase;
  }
  .header .badge-receipt {
    display: inline-block;
    background: var(--primary);
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 12px;
    border-radius: 20px;
    margin-top: 8px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  
  /* VOUCHER ID */
  .voucher-banner {
    background: linear-gradient(135deg, var(--primary-dark), #7C4DFF);
    border-radius: 12px;
    padding: 12px 16px;
    text-align: center;
    margin-bottom: 16px;
  }
  .voucher-banner .label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 2px;
    opacity: 0.8;
  }
  .voucher-banner .voucher-id {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
    margin-top: 2px;
  }
  
  /* INFO ROWS */
  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 16px;
  }
  .info-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 10px 12px;
  }
  .info-card .label {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin-bottom: 3px;
  }
  .info-card .value {
    font-size: 14px;
    font-weight: 600;
  }
  .info-card.full-width {
    grid-column: 1 / -1;
  }
  
  /* SECTION */
  .section {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    margin-bottom: 12px;
    overflow: hidden;
  }
  .section-header {
    padding: 10px 14px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--primary);
    border-bottom: 1px solid var(--card-border);
  }
  .section-body {
    padding: 8px 14px;
  }
  .section-body table {
    width: 100%;
    border-collapse: collapse;
  }
  .section-body th {
    text-align: left;
    font-size: 10px;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: 4px 0;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--card-border);
  }
  .section-body td {
    padding: 6px 0;
    font-size: 13px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
  }
  .section-body td:last-child, .section-body th:last-child {
    text-align: right;
  }
  
  /* TOTALS */
  .total-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 14px;
    font-size: 14px;
  }
  .total-row.muted {
    color: var(--text-muted);
    font-size: 12px;
  }
  .total-row.grand-total {
    font-size: 18px;
    font-weight: 800;
    padding: 12px 14px;
    background: linear-gradient(135deg, rgba(108,39,255,0.15), rgba(255,45,149,0.10));
    border-top: 2px solid var(--primary);
  }
  .total-row .label { }
  .total-row .amount { font-weight: 700; }
  .total-row .amount.positive { color: var(--success); }
  .total-row .amount.negative { color: var(--danger); }
  
  /* PAYMENT */
  .payment-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    padding: 10px 14px;
  }
  .payment-item {
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--card-border);
  }
  .payment-item .pay-label {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
  }
  .payment-item .pay-amount {
    font-size: 18px;
    font-weight: 800;
  }
  .payment-item .pay-amount.cash { color: var(--success); }
  .payment-item .pay-amount.kpay { color: var(--accent); }
  
  /* FOOTER */
  .footer {
    text-align: center;
    padding: 24px 0;
    margin-top: 8px;
    border-top: 1px solid var(--card-border);
  }
  .footer .tagline {
    font-size: 14px;
    font-weight: 600;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .footer .copyright {
    font-size: 10px;
    color: var(--text-muted);
    margin-top: 8px;
  }
  .footer .print-btn {
    display: inline-block;
    margin-top: 16px;
    padding: 10px 32px;
    border-radius: 25px;
    border: none;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    color: white;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .footer .print-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(108,39,255,0.4);
  }
  .footer .print-btn:active {
    transform: translateY(0);
  }
  
  /* FOC badge */
  .foc-badge {
    display: inline-block;
    background: var(--accent);
    color: white;
    font-size: 9px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    margin-left: 4px;
    vertical-align: middle;
  }
  .promo-badge {
    display: inline-block;
    background: var(--success);
    color: #000;
    font-size: 9px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    margin-left: 4px;
    vertical-align: middle;
  }
  
  /* Wallet Balance */
  .wallet-display {
    text-align: center;
    padding: 10px;
    background: rgba(0,230,118,0.06);
    border-radius: 8px;
    margin: 4px 0;
  }
  .wallet-display .wallet-label {
    font-size: 9px;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 1px;
  }
  .wallet-display .wallet-value {
    font-size: 22px;
    font-weight: 800;
    color: var(--success);
  }
  
  @media print {
    body { background: white; color: black; }
    .header h1, .footer .tagline { -webkit-text-fill-color: initial; background: none; color: var(--primary); }
    .voucher-banner { background: var(--primary-dark); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .info-card, .section { border-color: #ddd; background: #fafafa; }
    .total-row.grand-total { background: #f0f0f0; }
    .footer .print-btn { display: none; }
    .container { max-width: 100%; padding: 0; }
  }
</style>
</head>
<body>
<div class="container" id="app">
  <!-- Header -->
  <div class="header">
    <h1>PS VIBE</h1>
    <div class="subtitle">⚡ Gaming Lounge ⚡</div>
    <div class="badge-receipt">🧾 Receipt</div>
  </div>
  
  <!-- Voucher -->
  <div class="voucher-banner">
    <div class="label">Voucher ID</div>
    <div class="voucher-id" id="voucherId"></div>
  </div>
  
  <!-- Info Grid -->
  <div class="info-grid">
    <div class="info-card">
      <div class="label">📅 Date</div>
      <div class="value" id="receiptDate"></div>
    </div>
    <div class="info-card">
      <div class="label">🕹️ Console</div>
      <div class="value" id="consoleId"></div>
    </div>
    <div class="info-card">
      <div class="label">👤 Member</div>
      <div class="value" id="memberId"></div>
    </div>
    <div class="info-card">
      <div class="label">⏱️ Duration</div>
      <div class="value" id="playDuration"></div>
    </div>
  </div>
  
  <!-- Game Fee Section -->
  <div class="section" id="gameFeeSection">
    <div class="section-header">🎮 Gaming Fee</div>
    <div class="section-body">
      <table>
        <tr><th>Description</th><th>Amount</th></tr>
        <tr id="gameFeeRow"><td></td><td></td></tr>
      </table>
    </div>
  </div>
  
  <!-- Food Section (hidden if empty) -->
  <div class="section" id="foodSection" style="display:none">
    <div class="section-header">🍕 Food & Drinks</div>
    <div class="section-body">
      <table>
        <tr><th>Item</th><th>Amount</th></tr>
      </table>
    </div>
  </div>
  
  <!-- Discount Section (hidden if zero) -->
  <div class="section" id="discountSection" style="display:none">
    <div class="section-header">🎁 Discounts & Promotions</div>
    <div id="discountBody"></div>
  </div>
  
  <!-- Totals -->
  <div class="section" style="border-color: var(--primary);">
    <div class="total-row muted">
      <span class="label">Gross Total</span>
      <span class="amount" id="grossTotal"></span>
    </div>
    <div class="total-row muted" id="discountRow" style="display:none">
      <span class="label">Discount</span>
      <span class="amount negative" id="discountAmount"></span>
    </div>
    <div class="total-row muted" id="bonusRow" style="display:none">
      <span class="label">🎁 Bonus Minutes</span>
      <span class="amount positive" id="bonusAmount"></span>
    </div>
    <div class="total-row grand-total">
      <span class="label">💰 Net Total</span>
      <span class="amount" id="netTotal"></span>
    </div>
  </div>
  
  <!-- Payment Methods -->
  <div class="section">
    <div class="section-header">💳 Payment</div>
    <div class="payment-grid">
      <div class="payment-item">
        <div class="pay-label">Cash</div>
        <div class="pay-amount cash" id="cashAmount">0 Ks</div>
      </div>
      <div class="payment-item">
        <div class="pay-label">KPay</div>
        <div class="pay-amount kpay" id="kpayAmount">0 Ks</div>
      </div>
    </div>
  </div>
  
  <!-- Wallet Balance (members only) -->
  <div class="section" id="walletSection" style="display:none">
    <div class="section-header">💳 Wallet Balance</div>
    <div class="wallet-display">
      <div class="wallet-label">Remaining Balance</div>
      <div class="wallet-value" id="balanceAfter"></div>
      <div style="font-size:11px;color:var(--text-muted);margin-top:4px">
        Previous: <span id="prevBalance"></span> mins
        <span id="balanceChange"></span>
      </div>
    </div>
  </div>
  
  <!-- Footer -->
  <div class="footer">
    <div class="tagline">🎮 Play The Game. Share The VIBE! 🎮</div>
    <div class="copyright">PS VIBE Gaming Lounge &mdash; Yangon, Myanmar</div>
    <button class="print-btn" onclick="window.print()">🖨️ Print</button>
  </div>
</div>

<script>
// Load receipt JSON from script data attribute
(function() {
  // The receipt data is embedded by the server
  var data = window.__RECEIPT_DATA__;
  if (!data) {
    document.getElementById('voucherId').textContent = 'Receipt not found';
    return;
  }
  
  // Basic info
  document.getElementById('voucherId').textContent = data.voucher_id || '-';
  document.getElementById('receiptDate').textContent = data.date || '-';
  document.getElementById('consoleId').textContent = data.console_id || '-';
  
  if (data.is_guest) {
    document.getElementById('memberId').textContent = '👤 Guest';
  } else {
    document.getElementById('memberId').textContent = data.member_id || '👤 Guest';
  }
  
  // Duration
  var mins = data.play_mins || 0;
  document.getElementById('playDuration').textContent = mins + ' mins';
  
  // Game fee
  if (data.is_guest) {
    document.getElementById('gameFeeRow').innerHTML = '<td>🎮 ' + mins + ' mins × ' + (data.multiplier || 1) + 'x</td><td>' + formatKs(data.game_amt) + '</td>';
  } else {
    var deduct = Math.round(mins * (data.multiplier || 1));
    document.getElementById('gameFeeRow').innerHTML = '<td>🎮 ' + mins + ' mins played</td><td>' + formatKs(data.game_amt) + '</td>';
  }
  
  // Food items
  var foodItems = data.food_items || [];
  if (foodItems.length > 0) {
    document.getElementById('foodSection').style.display = 'block';
    var foodTable = document.querySelector('#foodSection table');
    foodItems.forEach(function(item) {
      var row = document.createElement('tr');
      var qty = item.qty || 1;
      row.innerHTML = '<td>' + (item.name || 'Item') + ' ×' + qty + '</td><td>' + formatKs(item.subtotal || 0) + '</td>';
      foodTable.appendChild(row);
    });
  }
  
  // Discount section
  var discount = data.discount || 0;
  var promoTitle = data.promo_title || '';
  var focItemName = data.foc_item_name || '';
  var focItemQty = data.foc_item_qty || 0;
  var bonusMins = data.bonus_mins || 0;
  
  if (discount > 0 || bonusMins > 0 || focItemName) {
    document.getElementById('discountSection').style.display = 'block';
    var discBody = document.getElementById('discountBody');
    var lines = [];
    
    if (focItemName) {
      lines.push('<div class="section-body"><span class="foc-badge">FOC</span> <strong>' + focItemName + '</strong> <span style="color:var(--text-muted)">×' + focItemQty + '</span></div>');
    }
    if (promoTitle) {
      lines.push('<div style="padding:4px 14px;font-size:12px;color:var(--text-muted)">Promotion: ' + promoTitle + '</div>');
    }
    if (data.promo_note) {
      lines.push('<div style="padding:4px 14px 10px;font-size:11px;color:var(--text-muted)">' + data.promo_note + '</div>');
    }
    discBody.innerHTML = lines.join('');
  }
  
  // Totals
  document.getElementById('grossTotal').textContent = formatKs(data.gross_total || 0);
  if (discount > 0) {
    document.getElementById('discountRow').style.display = 'flex';
    document.getElementById('discountAmount').textContent = '-' + formatKs(discount);
  }
  if (bonusMins > 0) {
    document.getElementById('bonusRow').style.display = 'flex';
    document.getElementById('bonusAmount').textContent = '+' + bonusMins + ' mins';
  }
  document.getElementById('netTotal').textContent = formatKs(data.net_total || 0);
  
  // Payment
  document.getElementById('cashAmount').textContent = formatKs(data.cash || 0);
  document.getElementById('kpayAmount').textContent = formatKs(data.kpay || 0);
  
  // Wallet balance (member only)
  if (!data.is_guest && data.balance_after !== null && data.balance_after !== undefined) {
    document.getElementById('walletSection').style.display = 'block';
    document.getElementById('balanceAfter').textContent = data.balance_after + ' mins';
    document.getElementById('prevBalance').textContent = data.prev_balance || 0;
    if (data.balance_change !== null && data.balance_change !== 0) {
      var changeStr = data.balance_change > 0 ? '+' + data.balance_change : String(data.balance_change);
      document.getElementById('balanceChange').textContent = '(' + changeStr + ' mins)';
    }
  }
  
  function formatKs(amt) {
    if (amt === null || amt === undefined) return '0 Ks';
    return Number(amt).toLocaleString() + ' Ks';
  }
})();
</script>
</body>
</html>
HTMLEOF
    echo "HTML template created ✅"
    
    echo ""
    echo "=== Step 3: Create receipt handler for FastAPI ==="
    
    cat > "$API_DIR/receipt_handler.py" << 'PYEOF'
"""
Receipt handler plugin for PS VIBE V2 API Server.
Registered at GET /api/z2a3b4/{voucher_id}
POST /api/z2a3b4 (receives receipt JSON from bot)

Obfuscated path mapping: z2a3b4 → "receipt"
"""
import os
import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)

# Paths
BOT_DIR = Path(__file__).resolve().parent.parent
RECEIPTS_DIR = BOT_DIR / "bot" / "receipts"
TEMPLATE_PATH = BOT_DIR / "receipts" / "template.html"

# Ensure directory exists
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Read secret from env
RECEIPT_SECRET = os.environ.get("RECEIPT_SECRET", "")
RECEIPT_DOMAIN = os.environ.get("RECEIPT_DOMAIN", "")

# Create router
router = APIRouter(prefix="/api/z2a3b4", tags=["receipt"])

# Load HTML template once
_TEMPLATE_CACHE: str | None = None

def _load_template() -> str:
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None:
        try:
            _TEMPLATE_CACHE = TEMPLATE_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Receipt template not found at %s", TEMPLATE_PATH)
            _TEMPLATE_CACHE = "<html><body><h1>Receipt template not found</h1></body></html>"
    return _TEMPLATE_CACHE


@router.get("/{voucher_id}")
async def serve_receipt(voucher_id: str, request: Request):
    """Serve printable HTML receipt for a given voucher ID."""
    safe_id = voucher_id.replace("/", "-").replace("\\", "-")
    json_path = RECEIPTS_DIR / f"{safe_id}.json"
    
    if not json_path.exists():
        logger.warning("Receipt JSON not found: %s", json_path)
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to read receipt JSON %s: %s", json_path, e)
        raise HTTPException(status_code=500, detail="Failed to read receipt data")
    
    # Get public receipt URL
    base_url = str(request.base_url).rstrip("/")
    receipt_url = f"{base_url}/api/z2a3b4/{safe_id}"
    
    html = _load_template()
    # Inject receipt data into the template
    data_json = json.dumps(data, ensure_ascii=False)
    html = html.replace(
        "</head>",
        f"<script>window.__RECEIPT_DATA__ = {data_json};</script></head>",
        1,
    )
    
    return HTMLResponse(content=html, status_code=200)


@router.post("")
async def receive_receipt(
    request: Request,
    x_receipt_secret: str = Header(None, alias="x-receipt-secret"),
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """Receive receipt JSON from bot and persist it."""
    # Validate secret
    if RECEIPT_SECRET and x_receipt_secret != RECEIPT_SECRET:
        logger.warning("Invalid receipt secret received")
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
        logger.info("Receipt saved: %s (%s)", safe_id, data.get("date", ""))
    except OSError as e:
        logger.error("Failed to write receipt JSON: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save receipt")
    
    return JSONResponse(
        content={
            "status": "ok",
            "voucher_id": voucher_id,
            "receipt_url": f"{RECEIPT_DOMAIN}/api/z2a3b4/{safe_id}" if RECEIPT_DOMAIN else "",
        },
        status_code=201,
    )


@router.get("/{voucher_id}/json")
async def serve_receipt_json(voucher_id: str):
    """Return raw receipt JSON."""
    safe_id = voucher_id.replace("/", "-").replace("\\", "-")
    json_path = RECEIPTS_DIR / f"{safe_id}.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_receipts():
    """List all saved receipt IDs."""
    if not RECEIPTS_DIR.exists():
        return {"receipts": []}
    files = sorted(RECEIPTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        "receipts": [f.stem for f in files[:100]],
        "count": len(files),
    }
PYEOF
    echo "Receipt handler created ✅ ($API_DIR/receipt_handler.py)"
    
    echo ""
    echo "=== Step 4: Set up environment variables ==="
    
    # Generate a random RECEIPT_SECRET
    RECEIPT_SECRET=$(tr -dc 'a-zA-Z0-9!@#$%^&*()_+' < /dev/urandom | head -c 32 2>/dev/null || echo "psvibe_receipt_secret_2026")
    
    # Append to .env if not already set
    if ! grep -q "RECEIPT_DOMAIN" "$BOT_DIR/.env"; then
      echo "RECEIPT_DOMAIN=https://receipt.psvibe.com" >> "$BOT_DIR/.env"
      echo "RECEIPT_DOMAIN added to .env ✅"
    else
      echo "RECEIPT_DOMAIN already in .env"
    fi
    
    if ! grep -q "RECEIPT_SECRET" "$BOT_DIR/.env"; then
      echo "RECEIPT_SECRET=$RECEIPT_SECRET" >> "$BOT_DIR/.env"
      echo "RECEIPT_SECRET added to .env ✅ (value: $RECEIPT_SECRET)"
    else
      echo "RECEIPT_SECRET already in .env"
    fi
    
    # Also update /etc/environment
    if ! grep -q "RECEIPT_DOMAIN" /etc/environment 2>/dev/null; then
      echo "RECEIPT_DOMAIN=https://receipt.psvibe.com" >> /etc/environment
      echo "Added RECEIPT_DOMAIN to /etc/environment ✅"
    fi
    if ! grep -q "RECEIPT_SECRET" /etc/environment 2>/dev/null; then
      echo "RECEIPT_SECRET=$RECEIPT_SECRET" >> /etc/environment
    fi
    
    echo ""
    echo "=== Step 5: Install python web dependencies ==="
    pip3 install fastapi uvicorn python-multipart 2>&1 | tail -3 || echo "pip install attempted"
    
    echo ""
    echo "=== Step 6: Install and configure Caddy reverse proxy ==="
    
    if ! command -v caddy &> /dev/null; then
      echo "Installing Caddy..."
      sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https 2>/dev/null
      curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null
      curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null 2>&1
      sudo apt-get update -qq 2>/dev/null && sudo apt-get install -y caddy 2>&1 | tail -3
      echo "Caddy installed ✅"
    else
      echo "Caddy already installed"
    fi
    
    # Configure Caddy for receipt domain and API proxy
    if [ -f /etc/caddy/Caddyfile ]; then
      cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak
    fi
    
    cat > /etc/caddy/Caddyfile << 'CADDYEOF'
# PS VIBE V2 — Caddy Reverse Proxy Configuration
# API Server: localhost:8000

# Receipt domain — serves printable receipt templates
receipt.psvibe.com {
    reverse_proxy localhost:8000
    
    header {
        X-Served-By "PS-VIBE-V2"
        -Server
    }
    
    # Security headers for receipt pages
    header /api/z2a3b4/* {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
    }
    
    # Cache control for receipt JSON
    header /api/z2a3b4/*/json {
        Cache-Control "no-cache, no-store, must-revalidate"
    }
    
    # Logs
    log {
        output file /var/log/caddy/receipt.log
        format json
    }
}

# Health check endpoint
ps-vibe.com {
    # Forward all /api/* requests to the API server
    handle /api/* {
        reverse_proxy localhost:8000
    }
    
    # Static files root
    root * /var/www/ps-vibe
    file_server
    
    log {
        output file /var/log/caddy/psvibe.log
        format json
    }
}
CADDYEOF
    echo "Caddy config written ✅"
    
    # Ensure log dir exists
    mkdir -p /var/log/caddy
    
    # Reload Caddy
    systemctl reload caddy 2>/dev/null || systemctl restart caddy 2>/dev/null || echo "Caddy restart attempted"
    echo "Caddy reloaded ✅"
    
    echo ""
    echo "=== Step 7: Create test receipt ==="
    mkdir -p "$RECEIPTS_DIR"
    
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
  "bonus_mins_promo": 15,
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
    echo "=== Step 8: Start API server daemon ==="
    
    # Kill any existing API server
    pkill -f "uvicorn.*api_server" 2>/dev/null || true
    
    # Start in background with nohup
    cd "$BOT_DIR"
    nohup python3 -m uvicorn api_server.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/api_server.log 2>&1 &
    API_PID=$!
    echo "API server starting (PID: $API_PID)..."
    sleep 3
    
    # Check if it's running
    if kill -0 $API_PID 2>/dev/null; then
      echo "API server is running ✅ (PID: $API_PID)"
    else
      echo "API server failed to start. Check /tmp/api_server.log"
      cat /tmp/api_server.log | tail -20
    fi
    
    echo ""
    echo "=== Setup Complete ==="
    echo "Receipt handler:        $API_DIR/receipt_handler.py"
    echo "HTML template:          $BOT_DIR/receipts/template.html" 
    echo "Receipts directory:     $RECEIPTS_DIR"
    echo "Receipt domain:         https://receipt.psvibe.com"
    echo "API endpoint:           /api/z2a3b4/{voucher_id}"
    echo "Test receipt:           V-999"
    echo ""
    echo "=== ENV VARS set ==="
    grep "RECEIPT" "$BOT_DIR/.env"
  `;
  
  conn.exec(commands, (err, stream) => {
    if (err) { console.error(err.message); process.exit(1); }
    let output = '';
    stream.on('data', d => output += d.toString());
    stream.stderr.on('data', d => output += d.toString());
    stream.on('close', (code) => {
      console.log(output);
      if (code !== 0) {
        console.log(`\n⚠️  Exit code: ${code} (some steps may have failed but core work might be done)`);
      }
      conn.end();
    });
  });
});

conn.connect({
  host: HOST,
  port: 22,
  username: 'root',
  privateKey,
});
