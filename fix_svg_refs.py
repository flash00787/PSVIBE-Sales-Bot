#!/usr/bin/env python3
"""Fix SVG url references from %23 to #."""
with open('/root/psvibe_api_server/receipt_template.html') as f:
    t = f.read()
t = t.replace('url(%23lg)', 'url(#lg)')
t = t.replace('url(%23lg2)', 'url(#lg2)')
with open('/root/psvibe_api_server/receipt_template.html', 'w') as f:
    f.write(t)
print('Fixed SVG refs')
