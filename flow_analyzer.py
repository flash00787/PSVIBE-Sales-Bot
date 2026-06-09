#!/usr/bin/env python3
"""Bot Conversation Flow Analyzer — State Machine & Callback Chain Analysis

Scans python-telegram-bot handler modules to:
  1. Map state machine flows (all states, transitions, entry/exit points)
  2. Detect callback chains (which function calls which)
  3. Find async flow issues (missing await, wrong call patterns)
  4. Identify orphan handlers (registered but never used states)
  5. Generate a state flow summary report

Usage:
  python3 flow_analyzer.py --analyze          # Full analysis
  python3 flow_analyzer.py --states           # State map only
  python3 flow_analyzer.py --report           # Generate markdown report
  python3 flow_analyzer.py --check-await      # Check async patterns only
"""

import ast
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ─────────────────────────────────────────────
#  Data structures
# ─────────────────────────────────────────────

@dataclass
class FunctionInfo:
    name: str
    filepath: str
    line: int
    is_async: bool
    params: List[str] = field(default_factory=list)
    awaits: List[int] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    decorated_by: List[str] = field(default_factory=list)


@dataclass
class HandlerRegistration:
    handler_type: str
    state_name: Optional[str]
    callback_func: str
    filepath: str
    line: int
    is_entry: bool = False
    is_fallback: bool = False
    pattern: Optional[str] = None
    command: Optional[str] = None


@dataclass
class ImportInfo:
    module: str
    names: List[str]
    filepath: str
    line: int
    is_wildcard: bool = False


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _read_file_safe(filepath: str) -> Optional[str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _get_decorator_names(node: ast.AST) -> List[str]:
    names = []
    for deco in getattr(node, "decorator_list", []):
        if isinstance(deco, ast.Name):
            names.append(deco.id)
        elif isinstance(deco, ast.Call):
            if isinstance(deco.func, ast.Name):
                names.append(deco.func.id)
            elif isinstance(deco.func, ast.Attribute):
                names.append(deco.func.attr)
    return names


def _resolve_call_name(call: ast.Call) -> Optional[str]:
    if isinstance(call.func, ast.Name):
        return call.func.id
    elif isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


# ─────────────────────────────────────────────
#  Handler file analysis
# ─────────────────────────────────────────────

def analyze_handler(filepath: str) -> dict:
    """Parse a handler module, extracting functions, imports, and handler registrations."""
    content = _read_file_safe(filepath)
    if content is None:
        return {"functions": [], "imports": [], "handlers": [], "missing_awaits": [], "error": "cannot read file"}

    result: dict = {"functions": [], "imports": [], "handlers": [], "missing_awaits": []}

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {"functions": [], "imports": [], "handlers": [], "missing_awaits": [], "error": str(e)}

    lines = content.split("\n")
    functions: Dict[str, FunctionInfo] = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_async = isinstance(node, ast.AsyncFunctionDef)
            params = [a.arg for a in node.args.args]
            func = FunctionInfo(
                name=node.name, filepath=filepath, line=node.lineno,
                is_async=is_async, params=params, decorated_by=_get_decorator_names(node),
            )
            for child in ast.walk(node):
                if isinstance(child, ast.Await):
                    func.awaits.append(child.lineno)
                elif isinstance(child, ast.Call):
                    caller = _resolve_call_name(child)
                    if caller:
                        func.calls.append(caller)
            functions[node.name] = func

    result["functions"] = sorted(functions.values(), key=lambda f: f.line)

    # Imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            imports.append(ImportInfo(
                module=node.module or "", names=names, filepath=filepath,
                line=node.lineno, is_wildcard=("*" in names),
            ))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(ImportInfo(
                    module=alias.name, names=[alias.asname or alias.name],
                    filepath=filepath, line=node.lineno,
                ))
    result["imports"] = sorted(imports, key=lambda i: i.line)

    # Handler registrations in this file
    result["handlers"] = _detect_handler_registrations(filepath, content, lines)
    result["missing_awaits"] = _detect_missing_awaits(filepath, content, lines, functions)

    return result


def _detect_handler_registrations(filepath: str, content: str, lines: List[str]) -> List[HandlerRegistration]:
    """Detect telegram handler registrations using regex."""
    handlers: List[HandlerRegistration] = []

    # Separate patterns for each handler type:
    #   CommandHandler("cmd", func_name)
    #   MessageHandler(filters.X, func_name)
    #   CallbackQueryHandler(func_name, pattern=r"...")

    cmd_re = re.compile(
        r'CommandHandler\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)'
    )
    msg_re = re.compile(
        r'MessageHandler\s*\(\s*filters\.\w+[^,]*,\s*(\w+)'
    )
    cbq_re = re.compile(
        r'CallbackQueryHandler\s*\(\s*(\w+)\s*,\s*pattern\s*=\s*r?["\']([^"\']+)["\']'
    )

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        for m in cmd_re.finditer(line):
            handlers.append(HandlerRegistration(
                handler_type="CommandHandler", state_name=None,
                callback_func=m.group(2), filepath=filepath, line=i,
                command=m.group(1),
            ))

        for m in msg_re.finditer(line):
            func_name = m.group(1)
            # Skip bare 'filters' matches (false positives from complex filter expressions)
            if func_name == "filters":
                continue
            handlers.append(HandlerRegistration(
                handler_type="MessageHandler", state_name=None,
                callback_func=func_name, filepath=filepath, line=i,
            ))

        for m in cbq_re.finditer(line):
            handlers.append(HandlerRegistration(
                handler_type="CallbackQueryHandler", state_name=None,
                callback_func=m.group(1), filepath=filepath, line=i,
                pattern=m.group(2),
            ))

    # Tag with context (entry_points, states, fallbacks)
    in_entry = False
    in_states = False
    in_fallback = False

    # Also detect state-name: [Handler(...)] patterns
    state_assign_re = re.compile(r'^\s*(\w+)\s*:\s*\[')

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if "entry_points" in stripped and ("=[" in stripped or "= [" in stripped):
            in_entry, in_states, in_fallback = True, False, False
        elif "states" in stripped and ("={" in stripped or "= {" in stripped):
            in_entry, in_states, in_fallback = False, True, False
        elif "fallbacks" in stripped and ("=[" in stripped or "= [" in stripped):
            in_entry, in_states, in_fallback = False, False, True

        # Don't exit entry_points too early — the list spans multiple lines
        if in_entry and stripped.rstrip().endswith("],") and "entry_points" not in stripped:
            in_entry = False
        if in_fallback and stripped.rstrip().endswith("],") and "fallbacks" not in stripped:
            in_fallback = False
        if in_states and stripped.rstrip().endswith("},") and "states" not in stripped:
            in_states = False

        # Detect state name from line pattern: STATE_NAME: [Handler(...)]
        sm = state_assign_re.match(stripped)
        state_name = sm.group(1) if sm else None

        # Tag handlers at this line
        for h in handlers:
            if h.line == i:
                if state_name and in_states:
                    h.state_name = state_name
                if in_entry:
                    h.is_entry = True
                elif in_fallback:
                    h.is_fallback = True

    return handlers


def _detect_missing_awaits(filepath: str, content: str, lines: List[str],
                           functions: Dict[str, FunctionInfo]) -> List[dict]:
    """Detect calls to known async functions without await prefix."""
    missing = []
    known_async = {fn.name for fn in functions.values() if fn.is_async}

    for fn in functions.values():
        if not fn.is_async:
            continue

        # Get function body text
        try:
            body_lines = lines[fn.line - 1:]
            func_text_parts = []
            indent = None
            for fl in body_lines:
                if fl.strip() == "":
                    func_text_parts.append(fl)
                    continue
                cur_indent = len(fl) - len(fl.lstrip())
                if indent is None:
                    indent = cur_indent
                if cur_indent <= indent and fl.strip() and not fl.strip().startswith(("#", "@")):
                    break
                func_text_parts.append(fl)
            func_text = "\n".join(func_text_parts)
        except Exception:
            continue

        for afunc in known_async:
            if afunc == fn.name:
                continue
            # Match "afunc(" but not "await afunc(" and not ".afunc("
            pat = re.compile(r'(?<!\bawait\s)(?<!await\s)(?<!\.)\b' + re.escape(afunc) + r'\s*\(')
            for m in pat.finditer(func_text):
                line_offset = func_text[:m.start()].count("\n")
                missing.append({
                    "filepath": filepath,
                    "in_function": fn.name,
                    "called_function": afunc,
                    "line": fn.line + line_offset,
                    "context": func_text[max(0, m.start() - 40):m.end() + 40].strip(),
                })

    return missing


# ─────────────────────────────────────────────
#  State map building
# ─────────────────────────────────────────────

def _extract_botstate_enum(bot_dir: str) -> Dict[str, int]:
    """Extract BotState(IntEnum) values from bot/__init__.py."""
    init_py = os.path.join(bot_dir, "__init__.py")
    content = _read_file_safe(init_py)
    if not content:
        return {}

    state_values: Dict[str, int] = {}
    in_class = False

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("class BotState") and "IntEnum" in stripped:
            in_class = True
            continue
        if in_class:
            if stripped.startswith("class ") or (stripped == "" and in_class):
                # blank line after class might still be part of it — keep going
                # But a new class definition ends it
                if stripped.startswith("class "):
                    break
                continue
            m = re.match(r'^(\w+)\s*=\s*(\d+)\s*$', stripped)
            if m:
                state_values[m.group(1)] = int(m.group(2))

    return state_values


def build_state_map(handlers_dir: str, bot_dir: str) -> dict:
    """Analyze all handler files + bot/app.py for state machine mapping."""
    handler_path = Path(handlers_dir)
    bot_path = Path(bot_dir)

    # Python handler files (exclude backups)
    py_files = sorted([
        f for f in handler_path.glob("*.py")
        if f.name != "__init__.py"
        and not f.name.endswith(".bak")
        and not f.name.endswith(".test_backup")
    ])

    all_handlers: List[HandlerRegistration] = []
    all_functions: Dict[str, FunctionInfo] = {}
    all_imports: List[ImportInfo] = []
    all_missing_awaits: List[dict] = []
    file_analyses: Dict[str, dict] = {}

    # Analyze each handler file
    for fpath in py_files:
        analysis = analyze_handler(str(fpath))
        file_analyses[str(fpath)] = analysis
        all_handlers.extend(analysis.get("handlers", []))
        all_imports.extend(analysis.get("imports", []))
        all_missing_awaits.extend(analysis.get("missing_awaits", []))

        for func in analysis.get("functions", []):
            all_functions[func.name] = func

    # Also analyze bot/app.py for the main ConversationHandler
    app_py = bot_path / "app.py"
    if app_py.exists():
        app_analysis = analyze_handler(str(app_py))
        file_analyses[str(app_py)] = app_analysis
        all_handlers.extend(app_analysis.get("handlers", []))
        all_imports.extend(app_analysis.get("imports", []))
        all_missing_awaits.extend(app_analysis.get("missing_awaits", []))

        for func in app_analysis.get("functions", []):
            all_functions[func.name] = func

    # Also scan bot/__init__.py for functions (many are defined there)
    init_py = bot_path / "__init__.py"
    if init_py.exists():
        init_analysis = analyze_handler(str(init_py))
        file_analyses[str(init_py)] = init_analysis
        all_imports.extend(init_analysis.get("imports", []))
        for func in init_analysis.get("functions", []):
            if func.name not in all_functions:
                all_functions[func.name] = func

    # Extract BotState enum values
    state_values = _extract_botstate_enum(bot_dir)

    # Build state map
    states: Dict[str, dict] = {}
    entry_points = [h for h in all_handlers if h.is_entry]
    fallbacks = [h for h in all_handlers if h.is_fallback]
    state_handlers = [h for h in all_handlers if not h.is_entry and not h.is_fallback]

    for h in state_handlers:
        sn = h.state_name or "UNKNOWN"
        if sn not in states:
            states[sn] = {"value": None, "handlers": [], "location": None}
        states[sn]["handlers"].append(h)
        if h.callback_func in all_functions:
            states[sn]["location"] = all_functions[h.callback_func].filepath

    # Populate state values from BotState
    for sn, sv in state_values.items():
        if sn in states:
            states[sn]["value"] = sv
        else:
            states[sn] = {"value": sv, "handlers": [], "location": None}

    # Detect orphans: BotState entries not used in any handler registration
    used_states = {h.state_name for h in all_handlers if h.state_name}
    orphan_states = [sn for sn in state_values if sn not in used_states]

    # Detect transitions (function call chains)
    transitions = _detect_transitions(all_functions, entry_points, fallbacks, states)

    total_files = len(py_files)
    if app_py.exists():
        total_files += 1

    return {
        "states": states,
        "entry_points": entry_points,
        "fallbacks": fallbacks,
        "all_handlers": all_handlers,
        "functions": all_functions,
        "imports": all_imports,
        "missing_awaits": all_missing_awaits,
        "orphan_states": orphan_states,
        "state_transitions": transitions,
        "files_analyzed": total_files,
        "file_analyses": file_analyses,
    }


def _detect_transitions(
    functions: Dict[str, FunctionInfo],
    entry_points: List[HandlerRegistration],
    fallbacks: List[HandlerRegistration],
    states: Dict[str, dict],
) -> List[Tuple[str, str, str]]:
    """Detect state transitions from function call chains."""
    transitions: List[Tuple[str, str, str]] = []

    for ep in entry_points:
        transitions.append(("ENTRY", ep.callback_func, ep.handler_type))

    for fb in fallbacks:
        transitions.append(("ANY_STATE", fb.callback_func, f"FALLBACK:{fb.handler_type}"))

    for state_name, state_info in states.items():
        for h in state_info.get("handlers", []):
            func = functions.get(h.callback_func)
            if func:
                for called in func.calls:
                    transitions.append((h.callback_func, called, "CALL"))

    return transitions


# ─────────────────────────────────────────────
#  Circular import detection
# ─────────────────────────────────────────────

def analyze_circular_imports(handlers_dir: str) -> List[dict]:
    """Check for circular import patterns."""
    handler_dir = Path(handlers_dir)
    py_files = sorted([
        f for f in handler_dir.glob("*.py")
        if f.name != "__init__.py"
        and not f.name.endswith(".bak")
        and not f.name.endswith(".test_backup")
    ])

    imports_graph: Dict[str, Set[str]] = defaultdict(set)

    for fpath in py_files:
        content = _read_file_safe(str(fpath))
        if not content:
            continue
        fname = fpath.name
        for m in re.finditer(r'from\s+(bot\.handlers\.\w+)\s+import', content):
            imports_graph[fname].add(m.group(1).split(".")[-1] + ".py")
        for m in re.finditer(r'from\s+bot\.handlers\s+import', content):
            # "from bot.handlers import foo, bar"
            # Just record all referenced module names
            pass

    circular = []
    for fname, deps in imports_graph.items():
        for dep in deps:
            if dep in imports_graph and fname in imports_graph[dep]:
                circular.append({"from": fname, "to": dep, "type": "bidirectional"})

    return circular


# ─────────────────────────────────────────────
#  Report generation
# ─────────────────────────────────────────────

def _compute_chain_depth(functions: Dict[str, FunctionInfo]) -> int:
    """Compute max callback chain depth via DFS with cycle detection."""
    visited: Set[str] = set()
    memo: Dict[str, int] = {}

    def dfs(func_name: str, path: Set[str]) -> int:
        if func_name in memo:
            return memo[func_name]
        if func_name in path:
            return 1
        path.add(func_name)
        func = functions.get(func_name)
        if not func:
            path.discard(func_name)
            return 1
        max_sub = 0
        for called in func.calls:
            if called in functions:
                sub = dfs(called, path)
                max_sub = max(max_sub, sub)
        path.discard(func_name)
        depth = 1 + max_sub
        memo[func_name] = depth
        return depth

    max_depth = 0
    for fn in functions:
        depth = dfs(fn, set())
        max_depth = max(max_depth, depth)
    return max_depth


def generate_flow_report(state_map: dict, output_path: Optional[str] = None) -> str:
    """Generate a comprehensive markdown flow analysis report."""
    lines = []
    lines.append("# 🤖 PS VIBE Bot — Flow Analysis Report")
    lines.append("")
    lines.append(f"**Files Analyzed:** {state_map['files_analyzed']}")
    lines.append(f"**Total Handler Registrations:** {len(state_map['all_handlers'])}")
    lines.append(f"**Entry Points:** {len(state_map['entry_points'])}")
    lines.append(f"**Fallback Handlers:** {len(state_map['fallbacks'])}")
    lines.append(f"**State States:** {len(state_map['states'])}")
    lines.append(f"**Orphan BotState entries:** {len(state_map['orphan_states'])}")
    lines.append(f"**Missing Await Warnings:** {len(state_map['missing_awaits'])}")
    lines.append(f"**Max Callback Chain Depth:** {_compute_chain_depth(state_map['functions'])}")
    lines.append("")

    # ── Entry Points ──
    lines.append("## 🚪 Entry Points")
    lines.append("")
    lines.append("| Type | Command/Pattern | Function |")
    lines.append("|------|-----------------|----------|")
    for ep in sorted(state_map["entry_points"], key=lambda h: h.callback_func):
        trigger = ep.command or ep.pattern or "—"
        lines.append(f"| {ep.handler_type} | `{trigger}` | `{ep.callback_func}` |")
    lines.append("")

    # ── State Map ──
    lines.append("## 📊 State Machine Map (BotState Enum → Handler)")
    lines.append("")
    lines.append("| State | Value | Handler Function(s) | Module |")
    lines.append("|-------|-------|---------------------|--------|")
    for sn in sorted(state_map["states"].keys()):
        si = state_map["states"][sn]
        val = si.get("value", "N/A")
        hfuncs = ", ".join(f"`{h.callback_func}`" for h in si.get("handlers", [])) or "—"
        loc = os.path.relpath(si.get("location", "") or "—", "/root/psvibe-sales-bot") if si.get("location") else "—"
        lines.append(f"| `{sn}` | `{val}` | {hfuncs} | {loc} |")
    lines.append("")

    # ── Fallbacks ──
    lines.append("## 🆘 Fallback Handlers (accessible from any state)")
    lines.append("")
    lines.append("| Type | Command/Pattern | Function |")
    lines.append("|------|-----------------|----------|")
    for fb in sorted(state_map["fallbacks"], key=lambda h: h.callback_func):
        trigger = fb.command or fb.pattern or "—"
        lines.append(f"| {fb.handler_type} | `{trigger}` | `{fb.callback_func}` |")
    lines.append("")

    # ── Orphan States ──
    if state_map["orphan_states"]:
        lines.append("## ⚠️ Orphan BotState Entries — Defined in Enum but NOT in ConversationHandler")
        lines.append("")
        orphan_by_value = sorted(state_map["orphan_states"],
                                  key=lambda sn: state_map["states"].get(sn, {}).get("value", 999))
        lines.append("| State | Value |")
        lines.append("|-------|-------|")
        for sn in orphan_by_value:
            val = state_map["states"].get(sn, {}).get("value", "?")
            lines.append(f"| `{sn}` | `{val}` |")
        lines.append("")
    else:
        lines.append("## ✅ No Orphan BotState Entries Found")
        lines.append("")

    # ── Missing Await ──
    if state_map["missing_awaits"]:
        lines.append("## 🔴 Potential Missing `await` Calls")
        lines.append("")
        lines.append("| File | In Function | Called | Line |")
        lines.append("|------|------------|--------|------|")
        for m in state_map["missing_awaits"]:
            fname = os.path.basename(m.get("filepath", ""))
            lines.append(
                f"| {fname} | `{m.get('in_function','')}` | `{m.get('called_function','')}` | "
                f"{m.get('line','')} |"
            )
        lines.append("")
    else:
        lines.append("## ✅ No Missing `await` Patterns Detected")
        lines.append("")

    # ── Circular Imports ──
    circular = analyze_circular_imports(
        os.path.join(os.path.dirname(state_map["functions"].get("show_main_menu", FunctionInfo(name="", filepath="", line=0, is_async=False)).filepath or ""), "..", "..", "bot", "handlers")
    )
    # Better: get from parent of first function's directory
    first_func = next(iter(state_map["functions"].values()), None)
    handlers_dir_guess = "/root/psvibe-sales-bot/bot/handlers"
    if first_func and first_func.filepath:
        handlers_dir_guess = str(Path(first_func.filepath).parent)

    circular = analyze_circular_imports(handlers_dir_guess)
    if circular:
        lines.append("## 🔄 Circular Import Warnings")
        lines.append("")
        for c in circular:
            lines.append(f"- `{c['from']}` ↔ `{c['to']}` ({c['type']})")
        lines.append("")
    else:
        lines.append("## ✅ No Circular Import Patterns Detected")
        lines.append("")

    # ── Per-File Summary ──
    lines.append("## 📁 Per-File Summary")
    lines.append("")
    lines.append("| File | Functions | Handlers | Imports |")
    lines.append("|------|-----------|----------|---------|")
    for fpath in sorted(state_map.get("file_analyses", {}).keys()):
        analysis = state_map["file_analyses"][fpath]
        fname = os.path.relpath(fpath, "/root/psvibe-sales-bot") if "/root/psvibe-sales-bot" in fpath else os.path.basename(fpath)
        nf, nh, ni = len(analysis.get("functions", [])), len(analysis.get("handlers", [])), len(analysis.get("imports", []))
        lines.append(f"| {fname} | {nf} | {nh} | {ni} |")
    lines.append("")

    report = "\n".join(lines)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    return report


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bot Conversation Flow Analyzer")
    parser.add_argument("--handlers-dir", default="/root/psvibe-sales-bot/bot/handlers")
    parser.add_argument("--bot-dir", default="/root/psvibe-sales-bot/bot")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--states", action="store_true")
    parser.add_argument("--report", nargs="?", const="/tmp/flow_report.md")
    parser.add_argument("--check-await", action="store_true")
    parser.add_argument("--output", default="/root/coordination/findings/stage1_flow_analyzer.json")

    args = parser.parse_args()

    if not os.path.isdir(args.handlers_dir):
        print(f"ERROR: handlers dir not found: {args.handlers_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.bot_dir):
        print(f"ERROR: bot dir not found: {args.bot_dir}", file=sys.stderr)
        sys.exit(1)

    if args.check_await:
        sm = build_state_map(args.handlers_dir, args.bot_dir)
        missing = sm["missing_awaits"]
        print(f"=== Missing Await Analysis ({len(missing)} warnings) ===")
        for m in missing:
            fname = os.path.basename(m.get("filepath", ""))
            print(f"  {fname}:{m.get('line','')} — `{m.get('in_function','')}` calls `{m.get('called_function','')}`")
        return

    if args.states:
        sm = build_state_map(args.handlers_dir, args.bot_dir)
        print(f"=== State Map ===")
        print(f"States: {len(sm['states'])}, Entry: {len(sm['entry_points'])}, Fallback: {len(sm['fallbacks'])}")
        for sn in sorted(sm["states"].keys()):
            si = sm["states"][sn]
            print(f"  {sn} = {si.get('value','?')} → {[h.callback_func for h in si.get('handlers',[])]}")
        print(f"\nOrphans: {len(sm['orphan_states'])}")
        for s in sorted(sm['orphan_states']):
            print(f"  - {s}")
        return

    if args.report or args.analyze:
        sm = build_state_map(args.handlers_dir, args.bot_dir)
        report_path = args.report if isinstance(args.report, str) else "/tmp/flow_report.md"
        report = generate_flow_report(sm, report_path)
        print(report)
        print(f"\n✅ Report written to: {report_path}")

        if args.analyze:
            circular = analyze_circular_imports(args.handlers_dir)
            json_data = {
                "stage": 1,
                "tool": "flow_analyzer.py",
                "size_lines": len(Path(__file__).read_text().split("\n")),
                "handlers_analyzed": sm["files_analyzed"],
                "states_found": len(sm["states"]),
                "orphan_states": len(sm["orphan_states"]),
                "missing_await": len(sm["missing_awaits"]),
                "circular_imports": len(circular),
                "analysis_passed": True,
                "report_path": report_path,
                "details": {
                    "entry_points": len(sm["entry_points"]),
                    "fallbacks": len(sm["fallbacks"]),
                    "total_functions": len(sm["functions"]),
                    "total_handlers": len(sm["all_handlers"]),
                    "max_chain_depth": _compute_chain_depth(sm["functions"]),
                },
            }
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(json_data, f, indent=2)
            print(f"\n✅ JSON written to: {args.output}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
