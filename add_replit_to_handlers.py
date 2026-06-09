# Add _replit_get and _replit_post functions to handlers/__init__.py
# These are needed by 13 handler files but are currently only in bot/__init__.py
# Adding them here breaks the dependency on bot/__init__.py (which causes circular import)

path = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(path) as f:
    content = f.read()

# Check if _replit_get already exists
if '_replit_get' in content:
    print('_replit_get already in handlers/__init__.py - checking')
else:
    # Read from bot/__init__.py
    with open('/root/Sales-Tele-Bot_refactored/bot/__init__.py') as f:
        init_content = f.read()
    
    # Find _replit_get, _replit_post, _api_base definitions
    import re
    replit_funcs = {}
    for func_name in ['_api_base', '_replit_get', '_replit_post']:
        # Find the function
        idx = init_content.find(f'def {func_name}(')
        if idx != -1:
            # Find matching body (next def or end)
            rest = init_content[idx:]
            next_def = 99999
            for m in re.finditer(r'^def \w+\(', rest, re.MULTILINE):
                if m.start() > 0:  # Skip the function itself
                    next_def = m.start()
                    break
            
            body = rest[:next_def].strip()
            replit_funcs[func_name] = body
        else:
            print(f'❌ {func_name} not found in bot/__init__.py')
    
    if replit_funcs:
        # Also add the imports needed by these functions
        # Check what imports they need
        needed_imports = []
        for func_name, body in replit_funcs.items():
            # Find required modules
            if 'os.' in body and 'import os' not in content:
                needed_imports.append('os')
            if 'json.' in body and 'import json' not in content:
                needed_imports.append('json')
            if 'urllib' in body and 'urllib' not in content:
                needed_imports.append('from urllib.request import Request, urlopen')
                needed_imports.append('from urllib.error import HTTPError')
            if 'time.' in body and 'import time' not in content:
                needed_imports.append('time')
            if 'gspread' in body and 'gspread' not in content:
                needed_imports.append('gspread')
        
        # Add imports at top
        if needed_imports:
            import_section = '\n'.join(f'import {i}' if '.' not in i else i for i in needed_imports) + '\n\n'
            content = import_section + content
        
        # Add functions before shared helpers section
        divider = '\n# ========== Shared helpers for all handler files ==========\n'
        if divider in content:
            idx = content.index(divider)
            repl_funcs_text = '\n# ========== Replit API helpers (copied from bot/__init__.py) ==========\n'
            for func_name, body in replit_funcs.items():
                repl_funcs_text += body + '\n\n'
            content = content[:idx] + '\n' + repl_funcs_text + content[idx:]
        
        with open(path, 'w') as f:
            f.write(content)
        
        for func_name in replit_funcs:
            print(f'✅ Added {func_name}')

with open(path) as f:
    content = f.read()
print(f'\nHandlers/__init__.py now has _replit_get: {"_replit_get" in content}')
print(f'Handlers/__init__.py now has _replit_post: {"_replit_post" in content}')
