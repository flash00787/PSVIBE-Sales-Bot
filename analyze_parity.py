#!/usr/bin/env python3
"""Analyze parity between V1 monolithic main.py and V2 modular code."""

import re
import ast
import os

V1_PATH = '/tmp/audit_v1.py'
V2_PATHS = {
    'init': '/tmp/audit_v2_init.py',
    'app': '/tmp/audit_v2_app.py',
    'handlers': '/tmp/audit_v2_handlers.py',
}

def extract_functions_and_classes(filepath):
    """Extract all top-level function and class definitions from a Python file."""
    functions = {}
    classes = {}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get the decorators
                decorators = [d.id if isinstance(d, ast.Name) else 
                              d.attr if isinstance(d, ast.Attribute) else str(d)
                              for d in node.decorator_list]
                functions[node.name] = {
                    'lineno': node.lineno,
                    'decorators': decorators,
                    'args': [arg.arg for arg in node.args.args],
                    'is_async': isinstance(node, ast.AsyncFunctionDef)
                }
            elif isinstance(node, ast.AsyncFunctionDef):
                decorators = [d.id if isinstance(d, ast.Name) else 
                              d.attr if isinstance(d, ast.Attribute) else str(d)
                              for d in node.decorator_list]
                functions[node.name] = {
                    'lineno': node.lineno,
                    'decorators': decorators,
                    'args': [arg.arg for arg in node.args.args],
                    'is_async': True
                }
            elif isinstance(node, ast.ClassDef):
                classes[node.name] = {
                    'lineno': node.lineno,
                    'methods': [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                }
    except SyntaxError as e:
        print(f"  Syntax error in {filepath}: {e}")
    except Exception as e:
        print(f"  Error parsing {filepath}: {e}")
    return functions, classes

def extract_imports(filepath):
    """Extract all import statements."""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        for line in source.split('\n'):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                imports.append(stripped)
    except:
        pass
    return imports

def extract_google_sheets_access(filepath):
    """Find Google Sheets access patterns."""
    patterns = {
        'gspread': [],
        'sheets': [],
        'worksheet': [],
    }
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if 'gspread' in line.lower():
                patterns['gspread'].append((i+1, line.strip()))
            if 'sheet' in line.lower() or 'worksheet' in line.lower():
                patterns['sheets'].append((i+1, line.strip()))
            if 'Worksheet' in line:
                patterns['worksheet'].append((i+1, line.strip()))
    except:
        pass
    return patterns

def extract_telegram_patterns(filepath):
    """Find Telegram handler patterns."""
    patterns = {
        'handlers': [],
        'dispatcher': [],
        'message_handler': [],
        'callback_handler': [],
    }
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if 'MessageHandler' in line or 'message_handler' in line:
                patterns['message_handler'].append((i+1, line.strip()))
            if 'CallbackQueryHandler' in line or 'callback_query_handler' in line:
                patterns['callback_handler'].append((i+1, line.strip()))
            if 'Dispatcher' in line or 'dispatcher' in line:
                patterns['dispatcher'].append((i+1, line.strip()))
    except:
        pass
    return patterns

def extract_error_handling(filepath):
    """Extract error handling patterns."""
    patterns = {
        'try_except': 0,
        'logger': 0,
        'logging': 0,
        'print_error': 0,
    }
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            lines = content.split('\n')
        patterns['try_except'] = content.count('\n    try:') + content.count('\n        try:')
        patterns['logger'] = content.count('logger.')
        patterns['logging'] = content.count('logging.')
        patterns['print_error'] = content.count('print(') - content.count('#print')
    except:
        pass
    return patterns

def compare_source_lines(func_name, v1_path, v2_path, v1_funcs, v2_funcs):
    """Get source lines for a function from both files."""
    result = {}
    if func_name in v1_funcs:
        try:
            with open(v1_path, 'r') as f:
                lines = f.readlines()
            start = v1_funcs[func_name]['lineno'] - 1
            result['v1_start'] = start + 1
            # Read ~20 lines
            result['v1_snippet'] = ''.join(lines[start:start+25])
        except:
            pass
    if func_name in v2_funcs:
        try:
            with open(v2_path, 'r') as f:
                lines = f.readlines()
            start = v2_funcs[func_name]['lineno'] - 1
            result['v2_start'] = start + 1
            result['v2_snippet'] = ''.join(lines[start:start+25])
        except:
            pass
    return result

def find_different_implementations(v1_funcs, v2_funcs, v1_path, v2_paths):
    """Find functions in both but with different implementations."""
    common = set(v1_funcs.keys()) & set(v2_funcs.keys())
    diffs = []
    for func_name in sorted(common):
        v1_info = v1_funcs[func_name]
        # Find in which V2 file
        v2_info = None
        v2_file = None
        for key, path in v2_paths.items():
            if func_name in v2_funcs[key]:
                v2_info = v2_funcs[key][func_name]
                v2_file = path
                break
        
        if v2_info is None:
            continue
        
        # Compare args and decorators
        v1_args = set(v1_info['args'])
        v2_args = set(v2_info['args'])
        v1_decs = set(v1_info.get('decorators', []))
        v2_decs = set(v2_info.get('decorators', []))
        
        if v1_args != v2_args or v1_decs != v2_decs:
            diffs.append({
                'function': func_name,
                'v1_args': v1_info['args'],
                'v2_args': v2_info['args'],
                'v1_decorators': v1_info.get('decorators', []),
                'v2_decorators': v2_info.get('decorators', []),
                'v1_line': v1_info['lineno'],
                'v2_line': v2_info['lineno'],
                'v2_file': v2_file,
            })
    return diffs

def extract_all_call_expressions(filepath):
    """Extract function/method call names."""
    calls = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
    except:
        pass
    return calls

def extract_global_variables(filepath):
    """Extract module-level variable assignments."""
    globals_list = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        globals_list.append(target.id)
    except:
        pass
    return globals_list

def count_lines_of_code(filepath):
    """Count non-empty, non-comment lines."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
        return len(lines), code_lines
    except:
        return 0, 0

# === MAIN ANALYSIS ===
print("=" * 80)
print("V1 vs V2 CODE PARITY AUDIT")
print("=" * 80)

# 1. Extract functions
print("\n📊 Extracting functions from all files...")
v1_funcs, v1_classes = extract_functions_and_classes(V1_PATH)

v2_funcs = {}
v2_classes = {}
for key, path in V2_PATHS.items():
    if os.path.exists(path):
        f, c = extract_functions_and_classes(path)
        v2_funcs[key] = f
        v2_classes[key] = c
        print(f"  V2 {key}: {len(f)} functions, {len(c)} classes")

print(f"  V1 main.py: {len(v1_funcs)} functions, {len(v1_classes)} classes")

# Combine all V2 functions
v2_all_funcs = {}
for key, fdict in v2_funcs.items():
    for name, info in fdict.items():
        v2_all_funcs[name] = {**info, 'v2_file': key}

# 2. Line counts
print("\n📏 Line counts:")
v1_total, v1_code = count_lines_of_code(V1_PATH)
for key, path in V2_PATHS.items():
    if os.path.exists(path):
        total, code = count_lines_of_code(path)
        print(f"  V2 {key}: {total} lines ({code} code)")
print(f"  V1 main.py: {v1_total} lines ({v1_code} code)")

# 3. Functions only in V1
print("\n🔴 FUNCTIONS IN V1 BUT MISSING IN V2:")
v1_only = set(v1_funcs.keys()) - set(v2_all_funcs.keys())
# Filter out Python built-in patterns
filtered_v1_only = [f for f in sorted(v1_only) 
                    if not f.startswith('__') or f.startswith('__init__')]
for func in filtered_v1_only:
    if v1_funcs[func].get('is_async'):
        tag = "⏳async "
    else:
        tag = ""
    decs = f" [@{', @'.join(v1_funcs[func].get('decorators', []))}]" if v1_funcs[func].get('decorators') else ""
    print(f"  {tag}{func}{decs} (line {v1_funcs[func]['lineno']})")

# 4. Functions only in V2
print("\n🟢 FUNCTIONS IN V2 BUT NOT IN V1:")
v2_only = set(v2_all_funcs.keys()) - set(v1_funcs.keys())
for func in sorted(v2_only):
    if func.startswith('__'):
        continue
    v2_info = v2_all_funcs[func]
    tag = "⏳async " if v2_info.get('is_async') else ""
    decs = f" [@{', @'.join(v2_info.get('decorators', []))}]" if v2_info.get('decorators') else ""
    print(f"  {tag}{func}{decs} (V2/{v2_info['v2_file']}, line {v2_info['lineno']})")

# 5. Functions with different signatures
print("\n🟡 FUNCTIONS WITH DIFFERENT SIGNATURES:")
diffs = find_different_implementations(v1_funcs, v2_funcs, V1_PATH, V2_PATHS)
for d in diffs:
    v2_file = os.path.basename(d['v2_file'])
    v2_key = [k for k, v in V2_PATHS.items() if v == d['v2_file']][0]
    print(f"  {d['function']}:")
    print(f"    V1 args: {d['v1_args']}  decs: {d['v1_decorators']}  (line {d['v1_line']})")
    print(f"    V2 args: {d['v2_args']}  decs: {d['v2_decorators']}  ({v2_key}, line {d['v2_line']})")

# 6. Import comparison
print("\n📦 IMPORT COMPARISON:")
v1_imports = set(extract_imports(V1_PATH))
v2_all_imports = set()
for key, path in V2_PATHS.items():
    if os.path.exists(path):
        imps = extract_imports(path)
        v2_all_imports.update(imps)

v1_import_bases = set()
for imp in v1_imports:
    if ' import ' in imp:
        v1_import_bases.add(imp.split(' import ')[0].replace('from ', '').strip())
    else:
        v1_import_bases.add(imp.replace('import ', '').strip().split('.')[0])

v2_import_bases = set()
for imp in v2_all_imports:
    if ' import ' in imp:
        v2_import_bases.add(imp.split(' import ')[0].replace('from ', '').strip())
    else:
        v2_import_bases.add(imp.replace('import ', '').strip().split('.')[0])

v1_extra_imports = v1_import_bases - v2_import_bases
v2_extra_imports = v2_import_bases - v1_import_bases
print(f"  V1-only imports: {sorted(v1_extra_imports)}")
print(f"  V2-only imports: {sorted(v2_extra_imports)}")

# 7. Google Sheets access patterns
print("\n📊 GOOGLE SHEETS ACCESS PATTERNS:")
v1_gs = extract_google_sheets_access(V1_PATH)
v2_gs = {}
for key, path in V2_PATHS.items():
    if os.path.exists(path):
        v2_gs[key] = extract_google_sheets_access(path)

print(f"  V1: gspread refs={len(v1_gs['gspread'])}, sheet refs={len(v1_gs['sheets'])}")
for key, gs in v2_gs.items():
    print(f"  V2 {key}: gspread refs={len(gs['gspread'])}, sheet refs={len(gs['sheets'])}")

# 8. Telegram patterns
print("\n🤖 TELEGRAM HANDLER PATTERNS:")
v1_tg = extract_telegram_patterns(V1_PATH)
print(f"  V1: MessageHandler={len(v1_tg['message_handler'])}, CallbackQueryHandler={len(v1_tg['callback_handler'])}")

for key, path in V2_PATHS.items():
    if os.path.exists(path):
        tg = extract_telegram_patterns(path)
        print(f"  V2 {key}: msg={len(tg['message_handler'])}, cb={len(tg['callback_handler'])}")

# 9. Error handling
print("\n🛡️ ERROR HANDLING PATTERNS:")
v1_err = extract_error_handling(V1_PATH)
print(f"  V1: try/except blocks={v1_err['try_except']}, logger calls={v1_err['logger']}, logging calls={v1_err['logging']}")

v2_total_err = {'try_except': 0, 'logger': 0, 'logging': 0, 'print_error': 0}
for key, path in V2_PATHS.items():
    if os.path.exists(path):
        err = extract_error_handling(path)
        v2_total_err['try_except'] += err['try_except']
        v2_total_err['logger'] += err['logger']
        v2_total_err['logging'] += err['logging']
        v2_total_err['print_error'] += err['print_error']
print(f"  V2 total: try/except blocks={v2_total_err['try_except']}, logger calls={v2_total_err['logger']}, logging calls={v2_total_err['logging']}")

# 10. Global variables
print("\n🌐 GLOBAL VARIABLES:")
v1_globals = extract_global_variables(V1_PATH)
v2_all_globals = set()
for key, path in V2_PATHS.items():
    if os.path.exists(path):
        v2_all_globals.update(extract_global_variables(path))

print(f"  V1 globals: {len(v1_globals)}")
print(f"  V2 globals: {len(v2_all_globals)}")
v1_gset = set(v1_globals)
v2_gset = set(v2_all_globals)
print(f"  V1-only globals: {sorted(v1_gset - v2_gset)}")
print(f"  V2-only globals: {sorted(v2_gset - v1_gset)}")

# 11. Call patterns
print("\n📞 FUNCTION CALL PATTERNS:")
v1_calls = extract_all_call_expressions(V1_PATH)
v2_all_calls = set()
for key, path in V2_PATHS.items():
    if os.path.exists(path):
        v2_all_calls.update(extract_all_call_expressions(path))

v1_call_only = v1_calls - v2_all_calls
v2_call_only = v2_all_calls - v1_calls
print(f"  V1 unique call target count: {len(v1_calls)}")
print(f"  V2 unique call target count: {len(v2_all_calls)}")
print(f"  V1-only call targets: {len(v1_call_only)}")
print(f"  V2-only call targets: {len(v2_call_only)}")

# Show some V1-only calls that look relevant
relevant_v1_calls = sorted([c for c in v1_call_only 
                           if not c.startswith('_') and len(c) > 3])
print(f"  V1-only calls (sample, first 30): {relevant_v1_calls[:30]}")

# 12. Classes
print("\n🏗️ CLASSES:")
print(f"  V1 classes: {sorted(v1_classes.keys())}")
v2_all_classes = {}
for key, cd in v2_classes.items():
    for name, info in cd.items():
        v2_all_classes[name] = info
print(f"  V2 classes: {sorted(v2_all_classes.keys())}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
