#!/usr/bin/env python3
"""Fix app.py: remove old inline kora cmd route, keep router version"""
import re

with open('/root/psvibe_api_server/app.py', 'r') as f:
    lines = f.readlines()

# Remove the old inline @app.get("/api/kora/cmd/{command}") route and its function
new_lines = []
skip = False
skip_depth = 0
for i, line in enumerate(lines):
    # Start skipping when we see the old inline route
    if '@app.get("/api/kora/cmd/{command}")' in line:
        skip = True
        skip_depth = 0
        continue
    
    # Count indentation to find the end of the function
    if skip:
        if line.startswith('@app.') or (line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('async')):
            # New route decorator or top-level code found - stop skipping
            skip = False
            new_lines.append(line)
        elif line.strip() == '' and skip_depth > 3:
            # Empty line after function body
            skip = False
        else:
            skip_depth += 1
        continue
    
    new_lines.append(line)

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.writelines(new_lines)

print("Cleaned up old inline route")
print(f"Lines: {len(lines)} -> {len(new_lines)}")

# Verify
with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()
    
kora_refs = [l for l in content.split('\n') if 'kora' in l.lower() and ('@app' in l.lower() or 'router' in l.lower() or 'import' in l.lower())]
for r in kora_refs:
    print(f"  Ref: {r.strip()}")
