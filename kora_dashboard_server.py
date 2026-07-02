#!/usr/bin/env python3
"""Kora Web Dashboard — PS VIBE real-time status page.
Zero-dependency: uses Python stdlib http.server + pymysql.
Runs on port 9092, auto-refreshes every 30s.
"""
import http.server
import json
import os
import time
from datetime import datetime, timezone, timedelta

# ── Timezone ──────────────────────────────────────────────────
MMT = timezone(timedelta(hours=6, minutes=30))  # Asia/Yangon

# ── DB Config ─────────────────────────────────────────────────
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "PsVibe@MySQL2024!",
    "database": "psvibe_api",
    "charset": "utf8mb4",
}
HEALTH_FILE = "/tmp/kora_health.json"


def db():
    import pymysql
    return pymysql.connect(**DB_CONFIG)


# ── Data Queries ──────────────────────────────────────────────

def get_today_numbers():
    """Revenue, active sessions, total bookings, members served."""
    conn = db()
    cur = conn.cursor()
    today = datetime.now(MMT).strftime("%Y-%m-%d")

    # Revenue today
    cur.execute(
        "SELECT COALESCE(SUM(net), 0) FROM sales_daily WHERE sale_date = CURDATE()"
    )
    revenue = float(cur.fetchone()[0])

    # Active sessions NOW
    cur.execute(
        "SELECT COUNT(*) FROM console_bookings "
        "WHERE status IN ('active','checked_in') AND booking_date = CURDATE()"
    )
    active_sessions = cur.fetchone()[0]

    # Total bookings today (done + active + checked_in + confirmed)
    cur.execute(
        "SELECT COUNT(*) FROM console_bookings WHERE booking_date = CURDATE()"
    )
    total_bookings = cur.fetchone()[0]

    # Done bookings
    cur.execute(
        "SELECT COUNT(*) FROM console_bookings "
        "WHERE booking_date = CURDATE() AND status = 'done'"
    )
    done_bookings = cur.fetchone()[0]

    # Cancelled
    cur.execute(
        "SELECT COUNT(*) FROM console_bookings "
        "WHERE booking_date = CURDATE() AND status = 'cancelled'"
    )
    cancelled = cur.fetchone()[0]

    # Unique members served today (from sales_daily or console_bookings)
    cur.execute(
        "SELECT COUNT(DISTINCT member_id) FROM console_bookings "
        "WHERE booking_date = CURDATE() AND member_id IS NOT NULL AND member_id != ''"
    )
    members_served = cur.fetchone()[0]

    conn.close()
    return {
        "revenue": revenue,
        "active_sessions": active_sessions,
        "total_bookings": total_bookings,
        "done": done_bookings,
        "cancelled": cancelled,
        "members_served": members_served,
    }


def get_service_status():
    """Read health file for service status dots."""
    try:
        with open(HEALTH_FILE) as f:
            health = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"timestamp": "N/A", "services": []}

    services = []
    for svc in health.get("services", []):
        status = svc.get("status", "unknown")
        if status == "active" and svc.get("sub_state") == "running":
            dot = "green"
        elif status == "active":
            dot = "yellow"
        else:
            dot = "red"
        services.append({
            "name": svc.get("name", "?"),
            "dot": dot,
            "status": status,
        })

    # Add docker containers
    for ctr in health.get("docker_containers", []):
        services.append({
            "name": ctr.get("name", "?"),
            "dot": "green" if ctr.get("running") else "red",
            "status": ctr.get("status", "?"),
        })

    ts = health.get("timestamp_mmt", health.get("timestamp", "N/A"))
    return {"timestamp": ts, "services": services}


def get_console_grid():
    """10 consoles — free/occupied status with game & time data."""
    conn = db()
    cur = conn.cursor()

    # Get console statuses
    cur.execute(
        "SELECT console_id, status, console_type, current_game, current_member, start_time "
        "FROM console_status ORDER BY console_id"
    )
    consoles = {}
    for row in cur.fetchall():
        cid, status, ctype, game, member, start = row
        consoles[cid] = {
            "console_id": cid,
            "type": ctype or "PS5",
            "status": status or "Free",
            "current_game": game or "",
            "current_member": member or "",
            "start_time": start,
            "time_remaining": "",
            "planned_end": None,
        }

    # Get active/checked_in/confirmed bookings today
    now = datetime.now(MMT)
    cur.execute(
        "SELECT console_id, status, game_name, planned_start, planned_end, "
        "planned_duration_mins, member_id "
        "FROM console_bookings "
        "WHERE booking_date = CURDATE() "
        "AND status IN ('active','checked_in','confirmed') "
        "ORDER BY planned_start"
    )
    for row in cur.fetchall():
        cid, status, game, pstart, pend, dur, member = row
        if cid in consoles:
            # Override with booking data
            consoles[cid]["status"] = status if status else consoles[cid]["status"]
            consoles[cid]["current_game"] = game or consoles[cid].get("current_game", "")
            consoles[cid]["current_member"] = member or consoles[cid].get("current_member", "")
            consoles[cid]["planned_end"] = pend

            if pend and status in ("active", "checked_in"):
                if pend.tzinfo is None:
                    pend_mmt = pend.replace(tzinfo=MMT)
                else:
                    pend_mmt = pend.astimezone(MMT)
                remaining = pend_mmt - now
                if remaining.total_seconds() > 0:
                    h = int(remaining.total_seconds() // 3600)
                    m = int((remaining.total_seconds() % 3600) // 60)
                    consoles[cid]["time_remaining"] = f"{h}h {m}m"
                else:
                    consoles[cid]["time_remaining"] = "Ended"
            elif status == "confirmed":
                # Show scheduled time
                if pstart:
                    if pstart.tzinfo is None:
                        pstart_mmt = pstart.replace(tzinfo=MMT)
                    else:
                        pstart_mmt = pstart.astimezone(MMT)
                    consoles[cid]["time_remaining"] = f"at {pstart_mmt.strftime('%H:%M')}"
    conn.close()

    # Sort and add display info
    result = []
    for cid in sorted(consoles.keys()):
        c = consoles[cid]
        st = c["status"]
        if st in ("Free", "free"):
            color = "green"
            label = "အားလွတ်"
        elif st in ("confirmed",):
            color = "orange"
            label = "Booked"
        elif st in ("active", "checked_in"):
            color = "red"
            label = "Active"
        else:
            color = "gray"
            label = st
        result.append({**c, "color": color, "label": label})
    return result


def get_timeline():
    """Bookings by hour for today — simple bar chart data."""
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT HOUR(planned_start) as hr, COUNT(*) as cnt "
        "FROM console_bookings "
        "WHERE booking_date = CURDATE() AND planned_start IS NOT NULL "
        "GROUP BY hr ORDER BY hr"
    )
    hours_data = {h: 0 for h in range(0, 24)}
    max_cnt = 1
    for row in cur.fetchall():
        h, cnt = row
        hours_data[h] = cnt
        if cnt > max_cnt:
            max_cnt = cnt
    conn.close()

    # Peak hour
    peak_hour = max(hours_data, key=hours_data.get)
    peak_count = hours_data[peak_hour]

    return {
        "hours": hours_data,
        "max": max_cnt,
        "peak_hour": peak_hour,
        "peak_count": peak_count,
    }


def get_payment_split():
    """Payment method split for today — parse payment_method string."""
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT payment_method, net FROM sales_daily WHERE sale_date = CURDATE()"
    )
    cash_total = 0.0
    kpay_total = 0.0
    wave_total = 0.0
    other_total = 0.0

    for row in cur.fetchall():
        method_str = (row[0] or "").strip()
        net = float(row[1] or 0)

        # Handle compound methods like "KPay:7000|Cash:17000"
        parts = method_str.split("|")
        for part in parts:
            part = part.strip()
            if ":" in part:
                pm, amount_str = part.split(":", 1)
                try:
                    amt = float(amount_str)
                except ValueError:
                    amt = 0
            else:
                pm = part
                amt = net  # fallback

            pm_lower = pm.lower().replace(" ", "")
            if "cash" in pm_lower or "cash" == pm_lower:
                cash_total += amt
            elif "kpay" in pm_lower or "kbz" in pm_lower:
                kpay_total += amt
            elif "wave" in pm_lower or "pay" in pm_lower:
                wave_total += amt
            else:
                other_total += amt

    conn.close()

    total = cash_total + kpay_total + wave_total + other_total
    if total <= 0:
        total = 1  # avoid div by zero

    return {
        "cash": {"amount": cash_total, "pct": round(cash_total / total * 100, 1)},
        "kpay": {"amount": kpay_total, "pct": round(kpay_total / total * 100, 1)},
        "wave": {"amount": wave_total, "pct": round(wave_total / total * 100, 1)},
        "other": {"amount": other_total, "pct": round(other_total / total * 100, 1)},
        "total": total,
    }


# ── HTML Generation ───────────────────────────────────────────

def format_mmk(amount):
    """Format as Myanmar Kyat with comma separators."""
    if amount >= 1_000_000:
        return f"{amount/1_000_000:.1f}M Ks"
    elif amount >= 1_000:
        return f"{amount/1_000:,.0f}K Ks"
    return f"{amount:,.0f} Ks"


def service_dot_svg(color):
    """Inline SVG dot."""
    return f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin-right:6px;"></span>'


def generate_html():
    """Generate full dashboard HTML."""
    now_str = datetime.now(MMT).strftime("%Y-%m-%d %H:%M:%S MMT")

    nums = get_today_numbers()
    services = get_service_status()
    consoles = get_console_grid()
    timeline = get_timeline()
    payments = get_payment_split()

    # ── Cards HTML ──
    cards = f"""
    <div class="cards">
      <div class="card card-revenue">
        <div class="card-icon">💰</div>
        <div class="card-value">{format_mmk(nums['revenue'])}</div>
        <div class="card-label">Revenue Today / ဒီနေ့ဝင်ငွေ</div>
      </div>
      <div class="card card-sessions">
        <div class="card-icon">🎮</div>
        <div class="card-value">{nums['active_sessions']}</div>
        <div class="card-label">Active Now / ကစားနေဆဲ</div>
      </div>
      <div class="card card-bookings">
        <div class="card-icon">📋</div>
        <div class="card-value">{nums['total_bookings']}</div>
        <div class="card-label">Total Bookings / စုစုပေါင်း<br>
          <small style="color:#4ade80">{nums['done']} done</small> ·
          <small style="color:#f87171">{nums['cancelled']} cancelled</small>
        </div>
      </div>
      <div class="card card-members">
        <div class="card-icon">👥</div>
        <div class="card-value">{nums['members_served']}</div>
        <div class="card-label">Members Served / ဝန်ဆောင်မှုပေး</div>
      </div>
    </div>
    """

    # ── Service Status HTML ──
    svc_rows = ""
    for svc in services["services"]:
        dot_color = {"green": "#22c55e", "yellow": "#eab308", "red": "#ef4444"}.get(svc["dot"], "#6b7280")
        svc_rows += f"""
        <div class="svc-row">
          <span class="svc-dot" style="background:{dot_color}"></span>
          <span class="svc-name">{svc['name']}</span>
          <span class="svc-status">{svc['status']}</span>
        </div>"""

    # ── Console Grid HTML ──
    console_cards = ""
    for c in consoles:
        clr = c["color"]
        bg_map = {"green": "rgba(34,197,94,0.15)", "orange": "rgba(234,179,8,0.15)", "red": "rgba(239,68,68,0.15)"}
        border_map = {"green": "#22c55e", "orange": "#eab308", "red": "#ef4444"}
        bg = bg_map.get(clr, "rgba(107,114,128,0.15)")
        border = border_map.get(clr, "#6b7280")
        game_display = c["current_game"] or "—"
        time_display = c["time_remaining"] or ""

        console_cards += f"""
        <div class="console-card" style="border-color:{border};background:{bg}">
          <div class="console-header">
            <span class="console-id">{c['console_id']}</span>
            <span class="console-type">{c['type']}</span>
          </div>
          <div class="console-badge" style="color:{border}">{c['label']}</div>
          <div class="console-game">{game_display}</div>
          <div class="console-time">⏱ {time_display}</div>
        </div>"""

    # ── Timeline HTML ──
    timeline_bars = ""
    for h in range(8, 24):  # 8 AM to 11 PM
        cnt = timeline["hours"][h]
        pct = (cnt / timeline["max"] * 100) if timeline["max"] > 0 else 0
        is_peak = h == timeline["peak_hour"]
        bar_color = "#f59e0b" if is_peak else "#6366f1"
        label = "★" if is_peak else ""
        timeline_bars += f"""
        <div class="timeline-col">
          <div class="timeline-bar" style="height:{int(pct)}%;background:{bar_color}" title="{cnt} bookings"></div>
          <div class="timeline-hour">{h:02d}:00</div>
          <div class="timeline-count">{cnt}{label}</div>
        </div>"""

    # ── Payment Split HTML ──
    pay_bars = ""
    pm_data = [
        ("Cash / ငွေသား", payments["cash"], "#22c55e"),
        ("KPay", payments["kpay"], "#6366f1"),
        ("WavePay", payments["wave"], "#06b6d4"),
        ("Other", payments["other"], "#6b7280"),
    ]
    for name, data, color in pm_data:
        if data["pct"] > 0:
            pay_bars += f"""
            <div class="pay-row">
              <span class="pay-label">{name}</span>
              <div class="pay-bar-track">
                <div class="pay-bar-fill" style="width:{data['pct']}%;background:{color}"></div>
              </div>
              <span class="pay-value">{data['pct']}% ({format_mmk(data['amount'])})</span>
            </div>"""

    # ── Full Page ──
    html = f"""<!DOCTYPE html>
<html lang="my">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="30">
  <title>Kora Dashboard — PS VIBE</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      min-height: 100vh;
      padding: 16px;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    
    /* Header */
    .header {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 12px 0 20px;
      border-bottom: 1px solid #1e293b;
      margin-bottom: 20px;
    }}
    .header h1 {{ font-size: 1.5rem; font-weight: 700; color: #f8fafc; }}
    .header h1 span {{ color: #6366f1; }}
    .header .time {{ font-size: 0.8rem; color: #94a3b8; }}
    .header .refresh {{ font-size: 0.7rem; color: #475569; }}
    
    /* Cards */
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .card {{
      background: #1e293b;
      border-radius: 12px;
      padding: 20px;
      border-left: 4px solid #6366f1;
      text-align: center;
    }}
    .card-revenue {{ border-left-color: #22c55e; }}
    .card-sessions {{ border-left-color: #f59e0b; }}
    .card-bookings {{ border-left-color: #6366f1; }}
    .card-members {{ border-left-color: #06b6d4; }}
    .card-icon {{ font-size: 1.8rem; margin-bottom: 6px; }}
    .card-value {{ font-size: 1.8rem; font-weight: 800; color: #f8fafc; }}
    .card-label {{ font-size: 0.75rem; color: #94a3b8; margin-top: 4px; line-height: 1.4; }}
    .card-label small {{ font-size: 0.7rem; }}
    
    /* Section titles */
    .section-title {{
      font-size: 1rem;
      font-weight: 700;
      color: #cbd5e1;
      margin: 24px 0 12px;
      padding-bottom: 6px;
      border-bottom: 1px solid #1e293b;
    }}
    
    /* Service Status */
    .svc-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 8px;
      margin-bottom: 20px;
    }}
    .svc-row {{
      display: flex; align-items: center;
      background: #1e293b;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 0.8rem;
    }}
    .svc-dot {{
      width: 8px; height: 8px; border-radius: 50%;
      margin-right: 8px; flex-shrink: 0;
    }}
    .svc-name {{ flex: 1; color: #e2e8f0; font-weight: 500; }}
    .svc-status {{ color: #64748b; font-size: 0.7rem; text-transform: uppercase; }}
    .svc-ts {{ font-size: 0.7rem; color: #475569; margin-bottom: 12px; }}
    
    /* Console Grid */
    .console-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 10px;
      margin-bottom: 24px;
    }}
    .console-card {{
      border: 2px solid #334155;
      border-radius: 10px;
      padding: 12px;
      text-align: center;
      transition: transform 0.2s;
    }}
    .console-card:hover {{ transform: translateY(-2px); }}
    .console-header {{
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 4px;
    }}
    .console-id {{ font-weight: 700; font-size: 0.9rem; color: #f8fafc; }}
    .console-type {{ font-size: 0.65rem; color: #64748b; background: #334155; padding: 2px 6px; border-radius: 4px; }}
    .console-badge {{ font-size: 0.75rem; font-weight: 700; margin: 6px 0; }}
    .console-game {{ font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px; }}
    .console-time {{ font-size: 0.7rem; color: #64748b; }}
    
    /* Timeline */
    .timeline {{ 
      display: flex; align-items: flex-end; gap: 2px;
      height: 140px; padding: 10px 0; margin-bottom: 24px;
    }}
    .timeline-col {{
      flex: 1; display: flex; flex-direction: column; align-items: center;
      height: 100%; justify-content: flex-end;
    }}
    .timeline-bar {{
      width: 100%; max-width: 36px; min-height: 2px;
      border-radius: 4px 4px 0 0; transition: height 0.3s;
    }}
    .timeline-hour {{ font-size: 0.6rem; color: #64748b; margin-top: 4px; }}
    .timeline-count {{ font-size: 0.6rem; color: #94a3b8; }}
    
    /* Payment Split */
    .pay-row {{
      display: flex; align-items: center; gap: 10px;
      margin-bottom: 10px;
      font-size: 0.8rem;
    }}
    .pay-label {{ width: 110px; color: #cbd5e1; font-weight: 500; flex-shrink: 0; }}
    .pay-bar-track {{
      flex: 1; height: 20px; background: #1e293b; border-radius: 10px;
      overflow: hidden;
    }}
    .pay-bar-fill {{
      height: 100%; border-radius: 10px; transition: width 0.5s;
      min-width: 2px;
    }}
    .pay-value {{ color: #94a3b8; font-size: 0.75rem; white-space: nowrap; min-width: 120px; text-align: right; }}
    .pay-total {{ font-size: 0.75rem; color: #64748b; margin-top: 8px; padding-top: 8px; border-top: 1px solid #1e293b; }}
    
    /* Footer */
    .footer {{
      text-align: center; padding: 20px; color: #475569;
      font-size: 0.7rem; margin-top: 20px; border-top: 1px solid #1e293b;
    }}
    
    /* Mobile */
    @media (max-width: 600px) {{
      .cards {{ grid-template-columns: repeat(2, 1fr); }}
      .console-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .svc-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .pay-row {{ flex-direction: column; align-items: flex-start; }}
      .pay-label {{ width: auto; }}
      .pay-bar-track {{ width: 100%; }}
      .pay-value {{ text-align: left; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>🎮 <span>Kora</span> Dashboard</h1>
        <div class="time">PS VIBE — Sanchaung</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:0.9rem">{now_str}</div>
        <div class="refresh">↻ auto-refresh 30s</div>
      </div>
    </div>

    <!-- 📊 TODAY'S NUMBERS -->
    <div class="section-title">📊 Today's Numbers / ဒီနေ့စာရင်း</div>
    {cards}

    <!-- 🟢 SERVICE STATUS -->
    <div class="section-title">🟢 Service Status / ဝန်ဆောင်မှုများ</div>
    <div class="svc-ts">Last check: {services['timestamp']}</div>
    <div class="svc-grid">{svc_rows}</div>

    <!-- 🎮 CONSOLE GRID -->
    <div class="section-title">🎮 Console Grid / စက်အခြေအနေ</div>
    <div class="console-grid">{console_cards}</div>

    <!-- ⏰ TODAY'S TIMELINE -->
    <div class="section-title">⏰ Today's Timeline (Peak: {timeline['peak_hour']:02d}:00 — {timeline['peak_count']} bookings)</div>
    <div class="timeline">{timeline_bars}</div>

    <!-- 💰 PAYMENT SPLIT -->
    <div class="section-title">💰 Payment Split / ငွေပေးချေမှု</div>
    {pay_bars}
    <div class="pay-total">Total: {format_mmk(payments['total'])}</div>

    <div class="footer">
      Kora Dashboard v1.0 · Port 9092 · PS VIBE · {now_str}
    </div>
  </div>
</body>
</html>"""
    return html.encode("utf-8")


# ── HTTP Server ───────────────────────────────────────────────

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "timestamp": datetime.now(MMT).isoformat()}).encode())
            return

        html = generate_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format, *args):
        """Quiet logging."""
        pass


def main():
    port = int(os.environ.get("DASHBOARD_PORT", "9092"))
    server = http.server.HTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"🔥 Kora Dashboard running on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
