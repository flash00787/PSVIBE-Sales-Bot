#!/usr/bin/env python3
"""
JS Analyzer — JavaScript/Node.js code analysis tool
Analyze monolithic Node.js bots (e.g. Three Brothers Construction bot).
Supports local files and remote files via SSH (Node.js ssh2 helper).

Usage:
  python3 js_analyzer.py --summary bot.js            python3 js_analyzer.py --scan-functions bot.js
  python3 js_analyzer.py --scan-commands bot.js       python3 js_analyzer.py --scan-deps bot.js
  python3 js_analyzer.py --structure bot.js           python3 js_analyzer.py --find "keyword" bot.js
  python3 js_analyzer.py --all bot.js                 python3 js_analyzer.py --all --ssh HOST:USER:KEY /opt/bot.js
"""

import argparse, re, subprocess, sys, os
from collections import defaultdict
from typing import List, Dict, Optional, Iterator

# ── Colors ───────────────────────────────────────────────────────────────────
C = {"R": "\033[91m", "G": "\033[92m", "Y": "\033[93m", "B": "\033[94m",
     "M": "\033[95m", "C": "\033[96m", "W": "\033[0m", "D": "\033[90m"}
def c(text, code): return f"{C.get(code,'')}{text}{C['W']}"

# ── Regex Patterns ──────────────────────────────────────────────────────────
RE_FUNC_DECL = re.compile(r'^\s*(?:export\s+)?(?:static\s+)?(?:async\s+)?function\s+([\w$]+)\s*\(', re.M)
RE_ARROW_FUNC = re.compile(r'^\s*(?:const|let|var)\s+([\w$]+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', re.M)
RE_CLASS_METHOD = re.compile(r'^\s*(?:static\s+)?(?:async\s+)?([\w$]+)\s*\([^)]*\)\s*\{', re.M)
RE_CLASS_DECL = re.compile(r'^\s*class\s+([\w$]+)', re.M)
RE_REQUIRE = re.compile(r"""(?:const|let|var)\s+(\{[\w\s,$:]+\}|[\w$]+)\s*=\s*require\(['"]([^'"]+)['"]\)""", re.M)
RE_REQUIRE_BARE = re.compile(r"""require\(['"]([^'"]+)['"]\)""")
RE_IMPORT = re.compile(r"""import\s+(?:\{[\w\s,$]+\}|[\w$]+|\*\s+as\s+[\w$]+)\s+from\s+['"]([^'"]+)['"]""", re.M)
RE_SECTION = re.compile(r'^\s*(?://|/\*)\s*={2,}\s*(.+?)\s*={2,}\s*(?:\*/)?\s*$', re.M)
RE_BOT_CMD = re.compile(r"""bot\.command\(['"]([\w_]+)['"]""")
RE_BOT_ON = re.compile(r"""bot\.on\(['"]([\w_]+)['"]""")
RE_BOT_ACTION = re.compile(r"""bot\.action\(['"]([\w_]+)['"]""")
RE_BOT_HEARS = re.compile(r"""bot\.(hears|onText)\((?:\/[^/]+\/|['"][^'"]+['"])""")
BLOCK_START = re.compile(r'/\*')
BLOCK_END = re.compile(r'\*/')

BUILTINS = {'fs','path','os','http','https','crypto','stream','events','util','url',
            'querystring','assert','buffer','child_process','net','tls','dgram','dns',
            'readline','cluster','zlib','timers','string_decoder','process','vm',
            'perf_hooks','async_hooks','worker_threads'}

# ── SSH Reader ───────────────────────────────────────────────────────────────
def ssh_read(host, user, key, rpath):
    script = f"""
const {{ Client }} = require('ssh2'); const fs = require('fs'); const conn = new Client();
conn.on('ready', () => {{ conn.sftp((e, sftp) => {{ if(e) {{ console.error('SFTP:'+e.message); conn.end(); process.exit(1); }}
  const c=[]; const st=sftp.createReadStream({repr(rpath)});
  st.on('data', d => c.push(d)); st.on('end', () => {{ process.stdout.write(Buffer.concat(c)); conn.end(); setTimeout(() => process.exit(0), 100); }});
  st.on('error', x => {{ console.error('STREAM:'+x.message); conn.end(); process.exit(1); }});
}})}});
conn.on('error', x => {{ console.error('SSH:'+x.message); process.exit(1); }});
conn.connect({{ host:{repr(host)}, port:22, username:{repr(user)}, privateKey:fs.readFileSync({repr(key)}), readyTimeout:15000 }});
"""
    try:
        r = subprocess.run(['node','-e',script], capture_output=True, timeout=30)
        if r.returncode != 0:
            print(c(f"SSH Error: {r.stderr.decode('utf-8','replace').strip()}", "R"), file=sys.stderr)
            sys.exit(1)
        return r.stdout.decode('utf-8','replace')
    except FileNotFoundError:
        print(c("Error: Node.js not found for SSH mode.", "R"), file=sys.stderr); sys.exit(1)
    except subprocess.TimeoutExpired:
        print(c("Error: SSH timeout (30s).", "R"), file=sys.stderr); sys.exit(1)

def read_lines(path, ssh=None):
    content = ssh_read(*ssh, path) if ssh else open(path, encoding='utf-8', errors='replace').read()
    return content.split('\n')

def _is_async(line):
    return 'async' in line.split('(')[0] if '(' in line else 'async ' in line

# ── Scanners ─────────────────────────────────────────────────────────────────
def scan_functions(lines):
    results, in_class, in_bc = [], None, False
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if BLOCK_START.search(line): in_bc = True
        if in_bc and BLOCK_END.search(line): in_bc = False; continue
        if in_bc or s.startswith('//'): continue
        cm = RE_CLASS_DECL.search(line)
        if cm: in_class = cm.group(1); continue
        if s in ('}',) or s.startswith('}'): in_class = None
        fm = RE_FUNC_DECL.search(line)
        if fm and not in_class:
            results.append({'line':i,'name':fm.group(1),'type':'function','async':_is_async(line)})
            continue
        am = RE_ARROW_FUNC.search(line)
        if am:
            results.append({'line':i,'name':am.group(1),'type':'arrow','async':_is_async(line)})
            continue
        if in_class:
            mm = RE_CLASS_METHOD.search(line)
            if mm:
                name = mm.group(1)
                results.append({'line':i,'name':name,'type':'constructor' if name=='constructor' else 'method',
                                'async':_is_async(line) if name!='constructor' else False,'context':in_class})
    return results

def scan_commands(lines):
    results = []
    for i, line in enumerate(lines, 1):
        if line.strip().startswith(('//','/*')): continue
        for pat, typ in [(RE_BOT_CMD,'command'),(RE_BOT_ON,'on'),(RE_BOT_ACTION,'action')]:
            m = pat.search(line)
            if m: results.append({'line':i,'type':typ,'name':m.group(1)}); break
        if 'bot.callbackQuery(' in line:
            results.append({'line':i,'type':'callbackQuery','name':'(anonymous)'}); continue
        m = RE_BOT_HEARS.search(line)
        if m: results.append({'line':i,'type':m.group(1),'name':'(pattern)'}); continue
        if 'bot.onText(' in line: results.append({'line':i,'type':'onText','name':'(pattern)'})
    return results

def scan_deps(lines):
    results = []
    for i, line in enumerate(lines, 1):
        m = RE_REQUIRE.search(line)
        if m: results.append({'line':i,'var':m.group(1).strip(),'module':m.group(2),'type':'require'}); continue
        m = RE_REQUIRE_BARE.search(line)
        if m and not RE_REQUIRE.search(line):
            results.append({'line':i,'var':'(none)','module':m.group(1),'type':'require'}); continue
        m = RE_IMPORT.search(line)
        if m: results.append({'line':i,'var':'(import)','module':m.group(1),'type':'import'})
    return results

def scan_structure(lines):
    return [{'line':i,'title':m.group(1).strip()} for i,line in enumerate(lines,1)
            for m in [RE_SECTION.search(line)] if m]

def find_pattern(lines, kw, ctx=2):
    results, pat = [], re.compile(re.escape(kw), re.I)
    for i, line in enumerate(lines, 1):
        if pat.search(line):
            rng = range(max(0,i-ctx-1), min(len(lines),i+ctx))
            results.append({'line':i,'text':line.strip(),'ctx':[(j+1,lines[j]) for j in rng]})
    return results

# ── Output ───────────────────────────────────────────────────────────────────
def hdr(title): print(f"\n{c('═'*70,'B')}\n{c(f'  {title}','bold')}{c('','B')}\n{c('═'*70,'B')}\n")

def print_summary(lines):
    total = len(lines); ne = sum(1 for l in lines if l.strip())
    cl = sum(1 for l in lines if l.strip().startswith(('//','/*')))
    funcs, cmds, deps, secs = scan_functions(lines), scan_commands(lines), scan_deps(lines), scan_structure(lines)
    classes = sum(1 for l in lines if RE_CLASS_DECL.search(l))
    async_n = sum(1 for f in funcs if f['async'])
    hdr("FILE SUMMARY")
    for k,v in [("Total lines:",total),("Code lines:",ne-cl),("Comment lines:",cl),("Blank lines:",total-ne),
                ("Functions:",f'{len(funcs)} ({async_n} async)'),
                ("Classes:",classes),("Bot handlers:",len(cmds)),("Dependencies:",len(deps)),("Sections:",len(secs))]:
        print(f'  {c(k,"bold")} {v}')
    if secs:
        print(f'\n  {c("Section Overview:","bold")}')
        for s in secs:
            print(f'    L{s["line"]:>5}  {s["title"]}')
    print()

def print_functions(funcs):
    if not funcs: print(c('  No functions found.','D')); return
    cnt = defaultdict(int)
    for f in funcs: cnt[f['type']] += 1
    async_n = sum(1 for f in funcs if f['async'])
    hdr('FUNCTION SCAN')
    parts = ', '.join(f'{v} {k}' for k,v in cnt.items())
    print(f'  Total: {len(funcs)} ({parts})  |  Async: {async_n}\n')
    for f in funcs:
        pre = c('async ','M') if f['async'] else ''
        ctx = f'  ({f["context"]})' if f.get('context') else ''
        fl, ft, fn = f['line'], f['type'], f['name']
        print(f'  {c(f"L{fl:>5}","D")} {c(f"[{ft}]","C")} {pre}{c(fn,"Y")}{ctx}')

def print_commands(cmds):
    if not cmds: print(c('  No bot commands found.','D')); return
    cnt = defaultdict(int)
    for cmd in cmds: cnt[cmd['type']] += 1
    hdr('TELEGRAM BOT COMMANDS & HANDLERS')
    parts = ', '.join(f'{v} {k}' for k,v in sorted(cnt.items()))
    print(f'  Total: {len(cmds)} ({parts})\n')
    for cmd in cmds:
        cl, ct, cn = cmd['line'], cmd['type'], cmd['name']
        print(f'  {c(f"L{cl:>5}","D")} {c(f"[{ct}]","M")} {c(cn,"G")}')

def print_deps(deps):
    if not deps: print(c('  No dependencies found.','D')); return
    npm = [d for d in deps if d['module'] not in BUILTINS and not d['module'].startswith('.')]
    local = [d for d in deps if d['module'].startswith('.')]
    builtin = [d for d in deps if d['module'] in BUILTINS]
    hdr('DEPENDENCIES')
    print(f'  Total: {len(deps)} (npm: {len(npm)}, local: {len(local)}, built-in: {len(builtin)})\n')
    if npm:
        print(c('  ── NPM Packages ──','bold'))
        for d in npm:
            dl, dv, dm = d['line'], d['var'], d['module']
            print(f'  {c(f"L{dl:>5}","D")} {c(dv,"Y")} ← {c(dm,"G")}')
    if local:
        print(c('\n  ── Local Modules ──','bold'))
        for d in local:
            dl, dv, dm = d['line'], d['var'], d['module']
            print(f'  {c(f"L{dl:>5}","D")} {c(dv,"Y")} ← {c(dm,"C")}')
    if builtin:
        print(c('\n  ── Node.js Built-ins ──','bold'))
        for d in builtin:
            dl, dv, dm = d['line'], d['var'], d['module']
            print(f'  {c(f"L{dl:>5}","D")} {c(dv,"Y")} ← {c(dm,"D")}')

def print_structure(secs):
    if not secs: print(c('  No section markers found.','D')); return
    hdr('FILE STRUCTURE')
    for i,s in enumerate(secs):
        mk = '└─' if i == len(secs)-1 else '├─'
        sl, st = s['line'], s['title']
        print(f'  {c(f"L{sl:>5}","D")} {mk} {c(st,"Y")}')

def print_find(results, kw):
    if not results: print(c(f'  No matches for \'{kw}\'.','D')); return
    hdr(f'SEARCH: \'{kw}\' — {len(results)} match(es)')
    esc = re.escape(kw)
    def hlfn(m): return c(m.group(1),'Y') + c('','R')
    for r in results:
        hl = re.sub(f'({esc})', hlfn, r['text'][:150], flags=re.I)
        line_key = r['line']
        print(f'  {c(f"L{line_key:>5}","D")}: {hl}')
        for ln, txt in r['ctx']:
            hl2 = re.sub(f'({esc})', lambda m: c(m.group(1),'Y')+c('','D'), txt, flags=re.I)
            pre = '→ ' if ln == line_key else '  '
            print(c(f'      {pre}{ln:>5}: {hl2}','D'))
        print()

def print_all(lines):
    print_summary(lines)
    print_functions(scan_functions(lines))
    print_structure(scan_structure(lines))
    print_commands(scan_commands(lines))
    print_deps(scan_deps(lines))

# ── CLI ──────────────────────────────────────────────────────────────────────
def parse_ssh(spec):
    parts = spec.split(':')
    if len(parts) == 3: return tuple(parts)
    elif len(parts) == 2: return (parts[0], parts[1], os.path.expanduser('~/.ssh/id_rsa'))
    print(c(f"Error: Invalid SSH spec '{spec}'. Use host:user[:keypath].","R"), file=sys.stderr); sys.exit(1)

def main():
    p = argparse.ArgumentParser(description="JS Analyzer — Analyze JS/Node.js bot code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  %(prog)s --all bot.js\n  %(prog)s --all --ssh 5.223.81.16:root:/root/.ssh/id_rsa /opt/bot.js")
    p.add_argument('file', nargs='?', help='JavaScript file to analyze')
    p.add_argument('--all', action='store_true', help='Run all scans')
    p.add_argument('--summary', action='store_true', help='Quick summary stats')
    p.add_argument('--scan-functions', action='store_true', help='Extract function definitions')
    p.add_argument('--scan-commands', action='store_true', help='Find Telegram bot patterns')
    p.add_argument('--scan-deps', action='store_true', help='Find require()/import statements')
    p.add_argument('--structure', action='store_true', help='Show section comment blocks')
    p.add_argument('--find', metavar='KEYWORD', help='Search with context')
    p.add_argument('--context', type=int, default=2, help='Context lines for --find')
    p.add_argument('--ssh', metavar='HOST:USER[:KEY]', help='Read via SSH (Node.js ssh2)')
    args = p.parse_args()
    if not args.file: p.print_help(); sys.exit(1)
    ssh_args = parse_ssh(args.ssh) if args.ssh else None
    any_scan = any([args.all, args.summary, args.scan_functions, args.scan_commands,
                    args.scan_deps, args.structure, args.find])
    if not any_scan: args.all = True
    lines = read_lines(args.file, ssh_args)
    print(c(f'\n  📄 File: {args.file}',"bold"))
    if ssh_args: print(c(f'  🔗 SSH:  {ssh_args[1]}@{ssh_args[0]}',"D"))
    if args.all: print_all(lines)
    else:
        if args.summary: print_summary(lines)
        if args.scan_functions: print_functions(scan_functions(lines))
        if args.structure: print_structure(scan_structure(lines))
        if args.scan_commands: print_commands(scan_commands(lines))
        if args.scan_deps: print_deps(scan_deps(lines))
        if args.find: print_find(find_pattern(lines, args.find, args.context), args.find)
    print()

if __name__ == '__main__': main()
