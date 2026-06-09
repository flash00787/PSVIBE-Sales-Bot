#!/usr/bin/env python3
"""Add PS VIBE logo to receipt template."""
with open('/root/psvibe_api_server/receipt_template.html') as f:
    html = f.read()

old = '''  <div class="header">
    <h1>PS VIBE</h1>
    <div class="subtitle">⚡ Gaming Lounge ⚡</div>
    <div class="badge-receipt" id="receiptBadge">🧾 Receipt</div>
  </div>'''

svg_logo = '''<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="24" cy="24" r="24" fill="url(%23lg)"/>
        <rect x="10" y="10" width="28" height="28" rx="8" fill="url(%23lg2)"/>
        <text x="24" y="31" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="900" fill="white">PV</text>
        <defs>
          <linearGradient id="lg" x1="0" y1="0" x2="48" y2="48">
            <stop stop-color="#6C27FF"/>
            <stop offset="1" stop-color="#FF2D95"/>
          </linearGradient>
          <linearGradient id="lg2" x1="0" y1="0" x2="28" y2="28">
            <stop stop-color="#7C4DFF"/>
            <stop offset="1" stop-color="#E040FB"/>
          </linearGradient>
        </defs>
      </svg>'''

new = f'''  <div class="header">
    <div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:8px">
      {svg_logo}
      <div style="text-align:left">
        <div style="font-size:20px;font-weight:800;color:var(--text);letter-spacing:1px">ps-vibe.com</div>
        <div style="font-size:10px;color:var(--text-muted);letter-spacing:1px">https://ps-vibe.com</div>
      </div>
    </div>
    <div class="badge-receipt" id="receiptBadge">🧾 Receipt</div>
  </div>'''

html = html.replace(old, new, 1)

with open('/root/psvibe_api_server/receipt_template.html', 'w') as f:
    f.write(html)

print('Logo added to receipt template ✅')
