#!/usr/bin/env python3
"""
PS VIBE Sales Bot — Architecture Mapper
Generates dependency graphs, detects circular imports, traces call chains.
"""

import ast
import os
import sys
import json
import argparse
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# ──────────────────────────────────────────────────────────────────
# AST Helpers
# ──────────────────────────────────────────────────────────────────

def _normalize_path(filepath: str, bot_dir: str) -> str:
    """Return path relative to bot_dir, with forward slashes."""
    try:
        return Path(filepath).resolve().relative_to(Path(bot_dir).resolve()).as_posix()
    except ValueError:
        return filepath

def _category(filepath: str) -> str:
    """Classify a module by its path."""
    p = filepath.lower()
    if '/handlers/' in p:
        return 'handler'
    if '/utils/' in p:
        return 'util'
    if '/data/' in p:
        return 'data'
    if 'sqlite' in p or 'db_manager' in p:
        return 'database'
    if 'customer_bot' in p:
        if 'api' in p:
            return 'api'
        return 'customer_bot'
    if 'constants' in p:
        return 'config'
    if 'helpers' in p:
        return 'util'
    if 'api_client' in p:
        return 'api'
    if 'app' in p or '__init__' in p or 'main.py' in p:
        return 'entry'
    if 'keep_alive' in p:
        return 'infra'
    if 'report' in p:
        return 'report'
    return 'other'


# ──────────────────────────────────────────────────────────────────
# 1. build_dependency_graph
# ──────────────────────────────────────────────────────────────────

def _resolve_import(module_name: str, from_package: str, all_py_modules: Set[str]) -> List[str]:
    """Resolve a bare module name to possible file paths in the project."""
    candidates = []
    # Convert dots to path separators
    rel = module_name.replace('.', '/')
    # Check if it matches a known .py file path (relative to bot_dir)
    for known in all_py_modules:
        # e.g. bot.handlers.members -> bot/handlers/members.py
        if known == f"{rel}.py" or known == f"{rel}/__init__.py":
            candidates.append(known)
        # Partial match: from bot.handlers import members -> bot/handlers/members.py
        if known.startswith(rel + '/') or known == f"{rel}.py":
            candidates.append(known)
    return candidates


def build_dependency_graph(bot_dir: str) -> Dict[str, Any]:
    """
    Parse all .py files in bot_dir via ast and build an import graph.
    Returns dict with nodes, edges, circular deps, stats.
    """
    bot_path = Path(bot_dir).resolve()
    py_files = list(bot_path.rglob('*.py'))
    # Exclude __pycache__, .mypy_cache, .git
    py_files = [f for f in py_files 
                if '__pycache__' not in str(f) 
                and '.mypy_cache' not in str(f)
                and '.git' not in str(f)]
    
    rel_files = {_normalize_path(str(f), bot_dir) for f in py_files}
    edges: List[Dict[str, str]] = []
    node_imports: Dict[str, List[str]] = defaultdict(list)
    star_imports: List[Dict[str, str]] = []
    unused_imports: List[Dict[str, str]] = []
    total_imports = 0

    for fpath in sorted(py_files):
        rel = _normalize_path(str(fpath), bot_dir)
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        try:
            tree = ast.parse(source, filename=str(fpath))
        except SyntaxError:
            continue

        # Collect all names defined in this module (top-level)
        defined_names: Set[str] = set()
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    defined_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    # Skip * imports
                    if alias.name != '*':
                        defined_names.add(name)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name
                    asname = alias.asname
                    total_imports += 1
                    # Resolve to project file
                    resolved = _resolve_import(imported, rel, rel_files)
                    if resolved:
                        for r in resolved:
                            edges.append({
                                'from': rel, 'to': r,
                                'type': 'import',
                                'name': alias.name,
                                'lineno': node.lineno
                            })
                            node_imports[rel].append(r)
                        if asname:
                            defined_names.add(asname)
                        else:
                            defined_names.add(imported.split('.')[0])
                    else:
                        # External import (not in project)
                        node_imports[rel].append(f'[external] {imported}')

            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue  # relative import without module
                for alias in node.names:
                    total_imports += 1
                    if alias.name == '*':
                        star_imports.append({
                            'from': rel,
                            'module': node.module,
                            'lineno': node.lineno
                        })
                        continue
                    resolved = _resolve_import(node.module, rel, rel_files)
                    if resolved:
                        for r in resolved:
                            edges.append({
                                'from': rel, 'to': r,
                                'type': 'from_import',
                                'name': alias.name,
                                'lineno': node.lineno
                            })
                            node_imports[rel].append(r)
                    else:
                        node_imports[rel].append(f'[external] {node.module}.{alias.name}')

        # Detect unused imports (simplistic: imported name never used in code)
        # We track names used in scope
        used_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # for module.func calls
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    if name not in used_names and name not in defined_names:
                        # check if it's actually unused (simple heuristic)
                        pass  # too noisy, skip for now
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    name = alias.asname or alias.name
                    if name not in used_names and name != alias.name:
                        unused_imports.append({
                            'file': rel,
                            'module': node.module,
                            'name': alias.name,
                            'lineno': node.lineno
                        })

    # Build adjacency for cycle detection
    adj: Dict[str, List[str]] = defaultdict(list)
    for edge in edges:
        adj[edge['from']].append(edge['to'])

    # DFS cycle detection
    circular_deps = _find_cycles(adj)

    # Build nodes list
    nodes: List[Dict[str, Any]] = []
    seen_nodes = set()
    for rel_path in sorted(rel_files):
        nodes.append({
            'path': rel_path,
            'category': _category(rel_path),
            'import_count': len([e for e in edges if e['from'] == rel_path]),
            'imported_by_count': len([e for e in edges if e['to'] == rel_path])
        })
        seen_nodes.add(rel_path)

    # Deduplicate edges
    unique_edges = []
    seen_edge = set()
    for e in edges:
        key = (e['from'], e['to'], e.get('name', ''))
        if key not in seen_edge:
            seen_edge.add(key)
            unique_edges.append(e)

    # Call chain depth analysis
    max_chain_depth = _max_chain_depth(adj)

    return {
        'nodes': nodes,
        'edges': unique_edges,
        'star_imports': star_imports,
        'unused_imports': unused_imports,
        'circular_deps': circular_deps,
        'total_imports': total_imports,
        'total_modules': len(rel_files),
        'max_chain_depth': max_chain_depth
    }


def _find_cycles(adj: Dict[str, List[str]]) -> List[List[str]]:
    """Detect circular dependencies using DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {node: WHITE for node in adj}
    cycles: List[List[str]] = []
    stack: List[str] = []

    def dfs(node: str):
        color[node] = GRAY
        stack.append(node)
        for neighbor in adj.get(node, []):
            if color.get(neighbor) == GRAY:
                # Found cycle
                cycle_start = stack.index(neighbor)
                cycles.append(list(stack[cycle_start:]) + [neighbor])
            elif color.get(neighbor) == WHITE:
                dfs(neighbor)
        stack.pop()
        color[node] = BLACK

    # Ensure all keys from edges are in color dict (collect first, update after)
    missing = []
    for from_node, to_nodes in list(adj.items()):
        for to_node in to_nodes:
            if to_node not in color:
                missing.append(to_node)
    
    for node in missing:
        if node not in color:
            color[node] = WHITE
            adj[node] = []

    for node in list(color.keys()):
        if color[node] == WHITE:
            dfs(node)

    return cycles


def _max_chain_depth(adj: Dict[str, List[str]]) -> int:
    """Calculate the longest import chain depth using iterative BFS with cycle protection."""
    # Since there may be cycles, use BFS with visited per path and depth limit
    nodes = list(adj.keys())
    for edges in adj.values():
        for e in edges:
            if e not in adj:
                adj[e] = []

    # Use BFS from each node with visited tracking; limit depth to prevent blowup
    max_depth = 0
    MAX_DEPTH = 50  # safety limit
    
    for start_node in nodes:
        # BFS tracking (node, depth, visited_set_frozenset)
        queue = deque([(start_node, 0, frozenset([start_node]))])
        seen_states = set()
        while queue:
            node, depth, visited = queue.popleft()
            if depth >= MAX_DEPTH:
                continue
            state_key = (node, len(visited))
            if state_key in seen_states:
                continue
            seen_states.add(state_key)
            
            max_depth = max(max_depth, depth)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1, visited | {neighbor}))

    return max_depth


# ──────────────────────────────────────────────────────────────────
# 2. map_function_calls
# ──────────────────────────────────────────────────────────────────

def map_function_calls(source_file: str, bot_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    For a given handler file, trace function call chains.
    Returns a dict with function -> list of called functions.
    Cross-module tracking if bot_dir is provided.
    """
    fpath = Path(source_file).resolve()
    if not fpath.exists():
        return {'error': f'File not found: {source_file}'}

    try:
        source = fpath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {'error': str(e)}

    try:
        tree = ast.parse(source, filename=str(fpath))
    except SyntaxError as e:
        return {'error': f'Syntax error: {e}'}

    # Collect all function defs
    func_calls: Dict[str, List[Dict[str, Any]]] = {}
    import_map: Dict[str, str] = {}  # local name -> module path

    # First pass: build import map
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split('.')[0]
                import_map[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    name = alias.asname or alias.name
                    if alias.name == '*':
                        # Mark star import
                        import_map[f'*{node.module}'] = node.module
                    else:
                        import_map[name] = f'{node.module}.{alias.name}'

    # Second pass: find function defs and calls within them
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    call_info = _extract_call_info(child, import_map)
                    if call_info:
                        calls.append(call_info)
            # Deduplicate calls within function
            unique_calls = []
            seen = set()
            for c in calls:
                key = (c.get('name'), c.get('module'))
                if key not in seen:
                    seen.add(key)
                    unique_calls.append(c)
            func_calls[node.name] = {
                'lineno': node.lineno,
                'calls': unique_calls,
                'call_count': len(unique_calls)
            }

    # Build call chain tree
    call_chains = _build_call_chains(func_calls)

    return {
        'file': str(fpath),
        'functions': func_calls,
        'call_chains': call_chains,
        'total_functions': len(func_calls),
        'import_map': dict(import_map)
    }


def _extract_call_info(call_node: ast.Call, import_map: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Extract name and module info from a call node."""
    info = {'lineno': call_node.lineno}
    
    if isinstance(call_node.func, ast.Name):
        info['name'] = call_node.func.id
        if call_node.func.id in import_map:
            info['module'] = import_map[call_node.func.id]
        info['type'] = 'direct'
    elif isinstance(call_node.func, ast.Attribute):
        parts = []
        obj = call_node.func
        while isinstance(obj, ast.Attribute):
            parts.append(obj.attr)
            obj = obj.value
        if isinstance(obj, ast.Name):
            parts.append(obj.id)
            full = '.'.join(reversed(parts))
            info['name'] = full
            info['module'] = import_map.get(obj.id, '')
            info['type'] = 'method'
        else:
            info['name'] = '.'.join(reversed(parts))
            info['type'] = 'chained'
    else:
        info['name'] = '<complex>'
        info['type'] = 'complex'
    
    return info


def _build_call_chains(func_calls: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build call chain tree from direct call data."""
    chains = []
    for fname, finfo in func_calls.items():
        chain = {
            'function': fname,
            'lineno': finfo['lineno'],
            'calls': []
        }
        for call in finfo.get('calls', []):
            chain['calls'].append({
                'name': call.get('name'),
                'module': call.get('module'),
                'type': call.get('type')
            })
        chains.append(chain)
    return chains


# ──────────────────────────────────────────────────────────────────
# 3. generate_mermaid_graph
# ──────────────────────────────────────────────────────────────────

def generate_mermaid_graph(output_path: str, graph_data: Optional[Dict[str, Any]] = None, bot_dir: str = '/root/psvibe-sales-bot'):
    """Generate a Mermaid.js dependency diagram."""
    if graph_data is None:
        graph_data = build_dependency_graph(bot_dir)

    lines = ['# PS VIBE Sales Bot — Dependency Graph', '', '```mermaid', 'graph TD']
    
    # Color map by category
    color_map = {
        'handler': '#ff9999',
        'util': '#99ccff',
        'data': '#99ff99',
        'database': '#ffcc99',
        'config': '#ffff99',
        'api': '#cc99ff',
        'entry': '#ff99cc',
        'customer_bot': '#ff9966',
        'report': '#99cccc',
        'infra': '#cccccc',
        'other': '#eeeeee'
    }

    # Node definitions
    node_ids: Dict[str, str] = {}
    for i, node in enumerate(graph_data.get('nodes', [])):
        node_id = f'N{i}'
        short_name = node['path'].replace('.py', '').replace('/', '_').replace('-', '_')
        node_ids[node['path']] = node_id
        color = color_map.get(node['category'], '#eeeeee')
        label = node['path'].replace('.py', '')
        lines.append(f'    {node_id}["{label}"]')
        lines.append(f'    style {node_id} fill:{color}')

    # Edge definitions
    arrow_map = {
        'import': '-->',
        'from_import': '-->',
        'star_import': '-.->'
    }

    for edge in graph_data.get('edges', []):
        from_id = node_ids.get(edge['from'])
        to_id = node_ids.get(edge['to'])
        if from_id and to_id:
            arrow = arrow_map.get(edge.get('type', 'import'), '-->')
            lines.append(f'    {from_id} {arrow} {to_id}')

    lines.append('```')
    lines.append('')
    lines.append('## Legend')
    lines.append('')
    lines.append('| Color | Category |')
    lines.append('|-------|----------|')
    for cat, color in sorted(color_map.items()):
        lines.append(f'| {color} | {cat} |')

    content = '\n'.join(lines)
    with open(output_path, 'w') as f:
        f.write(content)
    return output_path


# ──────────────────────────────────────────────────────────────────
# 4. generate_dot_graph
# ──────────────────────────────────────────────────────────────────

def generate_dot_graph(output_path: str, graph_data: Optional[Dict[str, Any]] = None, bot_dir: str = '/root/psvibe-sales-bot'):
    """Generate Graphviz DOT format."""
    if graph_data is None:
        graph_data = build_dependency_graph(bot_dir)

    lines = ['digraph PSVIBE_Sales_Bot {']
    lines.append('    rankdir=TB;')
    lines.append('    node [shape=box, style=filled];')
    lines.append('')

    color_map = {
        'handler': '#FF9999',
        'util': '#99CCFF',
        'data': '#99FF99',
        'database': '#FFCC99',
        'config': '#FFFF99',
        'api': '#CC99FF',
        'entry': '#FF99CC',
        'customer_bot': '#FF9966',
        'report': '#99CCCC',
        'infra': '#CCCCCC',
        'other': '#EEEEEE'
    }

    node_ids: Dict[str, str] = {}
    for i, node in enumerate(graph_data.get('nodes', [])):
        node_id = f'node{i}'
        node_ids[node['path']] = node_id
        label = node['path'].replace('.py', '').replace('/', '\\n')
        color = color_map.get(node['category'], '#EEEEEE')
        lines.append(f'    {node_id} [label="{label}", fillcolor="{color}"];')

    lines.append('')
    for edge in graph_data.get('edges', []):
        from_id = node_ids.get(edge['from'])
        to_id = node_ids.get(edge['to'])
        if from_id and to_id:
            style = 'dashed' if edge.get('type') == 'star_import' else 'solid'
            lines.append(f'    {from_id} -> {to_id} [style={style}];')

    lines.append('}')
    content = '\n'.join(lines)
    with open(output_path, 'w') as f:
        f.write(content)
    return output_path


# ──────────────────────────────────────────────────────────────────
# 5. generate_text_report
# ──────────────────────────────────────────────────────────────────

def generate_text_report(output_path: str, graph_data: Optional[Dict[str, Any]] = None, bot_dir: str = '/root/psvibe-sales-bot'):
    """Generate plain text dependency summary."""
    if graph_data is None:
        graph_data = build_dependency_graph(bot_dir)

    lines = []
    lines.append('=' * 70)
    lines.append('PS VIBE SALES BOT — ARCHITECTURE MAPPER REPORT')
    lines.append('=' * 70)
    lines.append('')

    # Summary stats
    lines.append('─── SUMMARY ───')
    lines.append('')
    lines.append(f'  Total modules analyzed:  {graph_data["total_modules"]}')
    lines.append(f'  Total imports tracked:   {graph_data["total_imports"]}')
    lines.append(f'  Unique import edges:     {len(graph_data["edges"])}')
    lines.append(f'  Circular dependencies:   {len(graph_data["circular_deps"])}')
    lines.append(f'  Star imports (*):        {len(graph_data["star_imports"])}')
    lines.append(f'  Unused imports detected: {len(graph_data["unused_imports"])}')
    lines.append(f'  Max import chain depth:  {graph_data["max_chain_depth"]}')
    lines.append('')

    # Module breakdown by category
    nodes_by_cat = defaultdict(list)
    for node in graph_data['nodes']:
        nodes_by_cat[node['category']].append(node)
    
    lines.append('─── MODULES BY CATEGORY ───')
    lines.append('')
    for cat in sorted(nodes_by_cat):
        lines.append(f'  [{cat}] ({len(nodes_by_cat[cat])} modules)')
        for n in sorted(nodes_by_cat[cat], key=lambda x: x['path']):
            lines.append(f'    - {n["path"]}  (imports: {n["import_count"]}, imported by: {n["imported_by_count"]})')
        lines.append('')

    # Top-level dependencies (most imported)
    lines.append('─── TOP DEPENDENCIES (most imported-by) ───')
    lines.append('')
    top = sorted(graph_data['nodes'], key=lambda x: x['imported_by_count'], reverse=True)[:10]
    for n in top:
        if n['imported_by_count'] > 0:
            lines.append(f'  {n["imported_by_count"]:>3} ← {n["path"]}')

    lines.append('')

    # Most heavy importers
    lines.append('─── HEAVIEST IMPORTERS ───')
    lines.append('')
    heavy = sorted(graph_data['nodes'], key=lambda x: x['import_count'], reverse=True)[:10]
    for n in heavy:
        if n['import_count'] > 0:
            lines.append(f'  {n["import_count"]:>3} → {n["path"]}')

    lines.append('')

    # Edge details
    lines.append('─── IMPORT EDGES ───')
    lines.append('')
    for edge in sorted(graph_data['edges'], key=lambda x: (x['from'], x['to'])):
        lines.append(f'  {edge["from"]:>40}  -->  {edge["to"]}  ({edge.get("type", "import")})')

    lines.append('')

    # Star imports
    if graph_data['star_imports']:
        lines.append('─── STAR IMPORTS (*) ───')
        lines.append('')
        for si in graph_data['star_imports']:
            lines.append(f'  {si["from"]:>40}  imports * from  {si["module"]}  (line {si["lineno"]})')
        lines.append('')

    # Circular dependencies
    if graph_data['circular_deps']:
        lines.append('─── CIRCULAR DEPENDENCIES ⚠ ───')
        lines.append('')
        for cycle in graph_data['circular_deps']:
            lines.append(f'  {" → ".join(cycle)}')
        lines.append('')
    else:
        lines.append('─── CIRCULAR DEPENDENCIES: NONE ✓ ───')
        lines.append('')

    # Unused imports
    if graph_data['unused_imports']:
        lines.append('─── POTENTIALLY UNUSED IMPORTS ───')
        lines.append('')
        for ui in sorted(graph_data['unused_imports'], key=lambda x: (x['file'], x['name'])):
            lines.append(f'  {ui["file"]}: from {ui["module"]} import {ui["name"]} (line {ui["lineno"]})')
        lines.append('')

    lines.append('=' * 70)
    lines.append('END OF REPORT')
    lines.append('=' * 70)

    content = '\n'.join(lines)
    with open(output_path, 'w') as f:
        f.write(content)
    return output_path


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='PS VIBE Architecture Mapper')
    parser.add_argument('--bot-dir', default='/root/psvibe-sales-bot',
                        help='Bot source directory (default: /root/psvibe-sales-bot)')
    parser.add_argument('--graph', nargs='?', const='/tmp/arch_diagram.md',
                        help='Generate Mermaid diagram. Optional output path.')
    parser.add_argument('--dep-text', nargs='?', const='/tmp/arch_report.txt',
                        help='Generate text dependency report. Optional output path.')
    parser.add_argument('--dot', nargs='?', const='/tmp/arch_graph.dot',
                        help='Generate DOT format. Optional output path.')
    parser.add_argument('--circular', action='store_true',
                        help='Find circular dependencies only.')
    parser.add_argument('--json', nargs='?', const='/tmp/arch_data.json',
                        help='Output full graph data as JSON.')
    parser.add_argument('--call-map', type=str,
                        help='Map function calls in a specific file.')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path for any format.')

    args = parser.parse_args()

    # If no action specified, show help
    if not any([args.graph, args.dep_text, args.dot, args.circular, args.json, args.call_map]):
        parser.print_help()
        sys.exit(0)

    bot_dir = args.bot_dir
    if not os.path.isdir(bot_dir):
        print(f'ERROR: Bot directory not found: {bot_dir}', file=sys.stderr)
        sys.exit(1)

    graph_data = build_dependency_graph(bot_dir)

    if args.graph:
        out = args.graph
        generate_mermaid_graph(out, graph_data, bot_dir)
        print(f'Mermaid diagram written to: {out}')

    if args.dep_text:
        out = args.dep_text
        generate_text_report(out, graph_data, bot_dir)
        print(f'Text report written to: {out}')

    if args.dot:
        out = args.dot
        generate_dot_graph(out, graph_data, bot_dir)
        print(f'DOT graph written to: {out}')

    if args.circular:
        cycles = graph_data['circular_deps']
        if cycles:
            print(f'⚠ Found {len(cycles)} circular dependencies:')
            for cycle in cycles:
                print(f'  {" → ".join(cycle)}')
        else:
            print('✓ No circular dependencies found.')

    if args.json:
        out = args.json
        with open(out, 'w') as f:
            json.dump(graph_data, f, indent=2, default=str)
        print(f'JSON data written to: {out}')

    if args.call_map:
        result = map_function_calls(args.call_map, bot_dir)
        print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
