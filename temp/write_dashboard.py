#!/usr/bin/env python3
"""Write the dashboard file from stdin"""
import sys, base64
data = sys.stdin.buffer.read()
with open('/root/.openclaw/workspace/kora_dashboard/index.html', 'wb') as f:
    f.write(data)
print(f'Written {len(data)} bytes')
