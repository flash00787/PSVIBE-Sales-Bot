#!/usr/bin/env python3
"""
Knowledge Graph — Entity-Relationship Graph for Kora's Memory System.
Scans all memory files and builds a relationship graph.
stdlib only: os, json, sys, re, datetime

Usage:
  python3 memory/knowledge_graph.py              # Quick status
  python3 memory/knowledge_graph.py --rebuild    # Full rebuild from scratch
  python3 memory/knowledge_graph.py --stats      # Graph statistics
  python3 memory/knowledge_graph.py --query Boss # Connections for an entity
  python3 memory/knowledge_graph.py --graph      # Full node-edge summary
"""

import os
import json
import sys
import re
from datetime import datetime, timezone

# ── Paths ────────────────────────────────────────────────────────────
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(WORKSPACE, 'memory')
GRAPH_FILE = os.path.join(MEMORY_DIR, 'knowledge-graph.json')

# ── Display labels ───────────────────────────────────────────────────
ENTITY_LABELS = {
    # People
    'boss':                    'Boss (Ko Aung Chan Myint)',
    'nova':                    'Nova AI',
    'ye-yint-oo':              'Ye Yint Oo',
    'chan-su-su-hlaing':       'Chan Su Su Hlaing',
    'ye-myat':                 'Ye Myat',
    'you-ko-htet':             'You Ko Htet',
    'kora':                    'Kora AI',
    # Projects
    'ps-vibe':                 'PS VIBE Gaming Lounge',
    'synergy-hub':             'Synergy Hub',
    'nova-bot':                'Nova Bot',
    'coco-bot':                'CoCo Bot',
    'gayzoelay-bot':           'GayZoeLay Bot',
    'agri-bot':                'Agri Bot',
    'personal-wallet-bot':     'Personal Wallet Bot',
    'sales-tele-bot':          'Sales Telegram Bot',
    # Technologies
    'mysql':                   'MySQL',
    'docker':                  'Docker',
    'vps':                     'VPS (DigitalOcean)',
    'google-sheets':           'Google Sheets',
    'telegram':                'Telegram Bot API',
    'python':                  'Python',
    'gemini-api':              'Gemini API',
    'google-drive-api':        'Google Drive API',
    'gmail-api':               'Gmail API',
    'openclaw':                'OpenClaw',
    'github':                  'GitHub',
    'caddy':                   'Caddy',
    'n8n':                     'n8n',
    'grok':                    'Grok (xAI)',
    'claude-sonnet':           'Claude Sonnet 4',
    'deepseek':                'DeepSeek',
    'openrouter':              'OpenRouter',
    'apparmor':                'AppArmor',
    'oauth2':                  'OAuth 2.0',
    'ssh':                     'SSH',
    # Concepts
    'memory-upgrade':          'Memory Upgrade',
    'subagent-tracking':       'Sub-agent Tracking',
    'coding-rules':            'Coding Rules (Pro Model)',
    'boot-protocol':           'Boot Protocol',
    'deploy-process':          'Deploy Process',
    'backup-strategy':         'Backup Strategy',
    'phase-2':                 'Memory Phase 2',
    'phase-3':                 'Memory Phase 3',
    'agent-coordination':      'Agent Coordination',
    'session-summary':         'Session Auto-Summary',
    'memory-index':            'Memory Topic Index',
    'priority-memory':         'Priority Memory System',
    'smart-pruning':           'Smart Pruning & Dedup',
    'daily-digest':            'Daily Digest',
    'git-backup':              'Git Auto-Backup',
    'knowledge-graph-concept': 'Knowledge Graph',
    'heartbeat-routine':       'Heartbeat Routine',
    'spawn-protocol':          'Spawn Protocol',
    'consolidator':            'Memory Consolidation',
}

# ── Entity definitions — id → {type, alias-list} ──────────────────
ENTITY_DEFS = [
    # ── People ──────────────────────────────────────────────
    ('boss',       'person',  ['Boss', 'Ko Aung Chan Myint', 'Aung Chan Myint',
                                'ကိုအောင်ချမ်းမြင့်', 'Osmo']),
    ('nova',       'person',  ['Nova']),
    ('ye-yint-oo', 'person',  ['Ye Yint Oo', 'Malboro', 'Ye Yint']),
    ('chan-su-su-hlaing', 'person', ['Chan Su Su Hlaing', 'Chan Su']),
    ('ye-myat',    'person',  ['Ye Myat', 'ရဲမြတ်']),
    ('you-ko-htet','person',  ['You Ko Htet', 'ယူကိုထက်']),
    ('kora',       'person',  ['Kora']),

    # ── Projects ────────────────────────────────────────────
    ('ps-vibe',         'project', ['PS VIBE', 'PS VIBE Gaming Lounge', 'psvibe',
                                     'PS5 Gaming Lounge']),
    ('synergy-hub',     'project', ['Synergy Hub']),
    ('nova-bot',        'project', ['Nova Bot', 'Nova project', 'nova_openclaw',
                                     'Nova Telegram config']),
    ('coco-bot',        'project', ['CoCo Bot', 'CoCo']),
    ('gayzoelay-bot',   'project', ['GayZoeLay Bot', 'GayZoeLay']),
    ('agri-bot',        'project', ['agri-bot', 'Agri Bot']),
    ('personal-wallet-bot', 'project', ['Personal-Wallet-Tele-Bot',
                                         'Personal Wallet Bot']),
    ('sales-tele-bot',  'project', ['Sales-Tele-Bot', 'psvibe-sale-bot',
                                     'Sales Telegram Bot', 'customer_bot']),

    # ── Technologies ────────────────────────────────────────
    ('mysql',            'technology', ['MySQL', 'Database']),
    ('docker',           'technology', ['Docker', 'docker-compose']),
    ('vps',              'technology', ['VPS', 'DigitalOcean', 'bot-server-01',
                                         '5.223.81.16']),
    ('google-sheets',    'technology', ['Google Sheets', 'gspread',
                                         'Google Sheets API', 'Spreadsheet']),
    ('telegram',         'technology', ['Telegram Bot', 'Telegram API',
                                         'BotFather', 'telegram.ext']),
    ('python',           'technology', ['Python', 'python3', 'Python 3']),
    ('gemini-api',       'technology', ['Gemini API', 'Gemini', 'gemini-embedding']),
    ('google-drive-api', 'technology', ['Google Drive API', 'Google Drive',
                                         'kora_drive_sa', 'Drive API']),
    ('gmail-api',        'technology', ['Gmail API', 'Gmail', 'send_email_api',
                                         'Gmail OAuth']),
    ('openclaw',         'technology', ['OpenClaw', 'openclaw agent']),
    ('github',           'technology', ['GitHub', 'git repo', 'Git']),
    ('caddy',            'technology', ['Caddy']),
    ('n8n',              'technology', ['n8n']),
    ('grok',             'technology', ['Grok', 'Grok 4.3', 'xAI']),
    ('claude-sonnet',    'technology', ['Claude Sonnet', 'Claude Sonnet 4',
                                         'Anthropic Claude']),
    ('deepseek',         'technology', ['DeepSeek', 'DeepSeek V4 Pro',
                                         'DeepSeek V4 Flash']),
    ('openrouter',       'technology', ['OpenRouter']),
    ('apparmor',         'technology', ['AppArmor', 'apparmor']),
    ('oauth2',           'technology', ['OAuth 2.0', 'oauth2client',
                                         'OAuth', 'oauth2']),
    ('ssh',              'technology', ['SSH', 'ssh2']),

    # ── Concepts ────────────────────────────────────────────
    ('memory-upgrade',       'concept', ['Memory Upgrade', 'Memory System',
                                          'Kora Memory Upgrade']),
    ('subagent-tracking',    'concept', ['Sub-agent Tracking', 'Sub-agent Journal',
                                          'Sub-agent Timeout', 'Active Tasks',
                                          'Sub-agent Tracking System']),
    ('coding-rules',         'concept', ['Coding Rules', 'Pro Model Only',
                                          'Coding Rule', 'Pro model for coding']),
    ('boot-protocol',        'concept', ['Boot Protocol', 'Session Startup',
                                          'boot_protocol']),
    ('deploy-process',       'concept', ['Deploy Process', 'deploy.sh',
                                          'rollback.sh']),
    ('backup-strategy',      'concept', ['Backup Strategy', 'Backup Inventory',
                                          'Backup Locations']),
    ('phase-2',              'concept', ['Phase 2 memory', 'Phase 2 upgrade',
                                          'Phase 2 memory upgrade']),
    ('phase-3',              'concept', ['Phase 3 memory', 'Phase 3 upgrade',
                                          'Phase 3 memory upgrade', 'Phase 3']),
    ('agent-coordination',   'concept', ['Agent Coordination',
                                          'Agent Coordination Pattern',
                                          'Coordination Pattern']),
    ('session-summary',      'concept', ['Session Summary', 'Session Auto-Summary',
                                          'session_summary']),
    ('memory-index',         'concept', ['Memory Index', 'Topic Search',
                                          'memory_index', 'memory-index']),
    ('priority-memory',      'concept', ['Priority Memory', 'Priority Levels',
                                          'Priority Memory System',
                                          'priority_engine']),
    ('smart-pruning',        'concept', ['Smart Pruning', 'Dedup',
                                          'memory_pruner']),
    ('daily-digest',         'concept', ['Daily Digest', 'Digest Generator',
                                          'daily_digest']),
    ('git-backup',           'concept', ['Git Auto-Backup', 'Git Backup',
                                          'git_backup', 'Git Auto Backup']),
    ('knowledge-graph-concept', 'concept', ['Knowledge Graph',
                                             'knowledge_graph',
                                             'knowledge-graph']),
    ('heartbeat-routine',    'concept', ['Heartbeat Routine',
                                          'Heartbeat Memory Maintenance',
                                          'heartbeat_routine']),
    ('spawn-protocol',       'concept', ['Spawn Protocol', 'Subagent Control',
                                          'subagent_ctl', 'Spawn Control']),
    ('consolidator',         'concept', ['Consolidator', 'Memory Consolidation',
                                          'Auto Consoli', 'consolidator']),
]

# ── Build lookup maps ──────────────────────────────────────────────
ENTITY_TYPE = {}       # id → type
ALIAS_TO_ID = {}       # lowercased-alias → id
for eid, etype, aliases in ENTITY_DEFS:
    ENTITY_TYPE[eid] = etype
    for alias in aliases:
        ALIAS_TO_ID[alias.lower()] = eid

# ── Relationship UI labels ─────────────────────────────────────────
REL_LABELS = {
    'owns':        'owns',
    'uses':        'uses',
    'related_to':  'related to',
    'implements':  'implements',
    'depends_on':  'depends on',
}

# ── Emoji by type ──────────────────────────────────────────────────
TYPE_EMOJI = {
    'person':     '👤',
    'project':    '🚀',
    'technology': '🔧',
    'concept':    '💡',
}


# ══════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════

def find_entities(text):
    """Return set of entity-ids mentioned anywhere in *text* (case-insensitive)."""
    lower = text.lower()
    found = set()
    for alias_lower, eid in ALIAS_TO_ID.items():
        if alias_lower in lower:
            found.add(eid)
    return found


def find_bold_entities(text):
    """Look for **bolded text** markers and return entity-ids matched."""
    found = set()
    for m in re.finditer(r'\*\*(.+?)\*\*', text):
        inner = m.group(1).strip().lower()
        if inner in ALIAS_TO_ID:
            found.add(ALIAS_TO_ID[inner])
    return found


def infer_relation(src_eid, tgt_eid):
    """Return the best relation string for a directed pair (src → tgt).
       Direction is fixed by type hierarchy: person > project > technology > concept.
       When types are equal we use alphabetical id ordering to keep edges stable."""
    st = ENTITY_TYPE.get(src_eid, 'unknown')
    tt = ENTITY_TYPE.get(tgt_eid, 'unknown')

    # Person → Project
    if st == 'person' and tt == 'project':
        return 'owns'
    # Person → Concept
    if st == 'person' and tt == 'concept':
        return 'implements'
    # Person → Technology
    if st == 'person' and tt == 'technology':
        return 'uses'
    # Project → Technology
    if st == 'project' and tt == 'technology':
        return 'uses'
    # Technology → Technology
    if st == 'technology' and tt == 'technology':
        return 'depends_on'
    # Concept → Concept
    if st == 'concept' and tt == 'concept':
        return 'related_to'
    # Concept → Technology or Concept → Project
    if st == 'concept' and tt in ('technology', 'project'):
        return 'related_to'
    # Project → Concept
    if st == 'project' and tt == 'concept':
        return 'related_to'
    # Person → Person
    if st == 'person' and tt == 'person':
        return 'related_to'
    # Project → Project
    if st == 'project' and tt == 'project':
        return 'related_to'

    return 'related_to'


# ══════════════════════════════════════════════════════════════════════
#  Scanner
# ══════════════════════════════════════════════════════════════════════

def collect_files():
    """Return list of (short_name, absolute_path) for files to scan."""
    files = []

    # Workspace root files (MEMORY.md, TOOLS.md, AGENTS.md)
    for name in ['MEMORY.md', 'TOOLS.md', 'AGENTS.md']:
        p = os.path.join(WORKSPACE, name)
        if os.path.isfile(p):
            files.append((name, p))

    # All markdown + json files inside memory/
    if os.path.isdir(MEMORY_DIR):
        for entry in sorted(os.listdir(MEMORY_DIR)):
            p = os.path.join(MEMORY_DIR, entry)
            if not os.path.isfile(p):
                continue
            if entry.endswith(('.md', '.json')):
                files.append((f'memory/{entry}', p))

    return files


def scan():
    """Scan all memory files and return a graph dict."""
    files = collect_files()
    nodes = {}                    # entity-id → type  (discovered nodes)
    file_entities = {}            # file-short-name → set-of-entity-ids
    # Edge accumulator: (src, tgt, relation) → max-weight
    edge_weights = {}

    for short_name, path in files:
        try:
            with open(path, 'r') as fh:
                raw = fh.read()
        except Exception:
            continue

        # ── Discover nodes from the whole file ────────────
        file_set = set()
        # explicit aliases
        file_set |= find_entities(raw)
        # bold markdown
        file_set |= find_bold_entities(raw)
        # ## headings → check if heading text matches an entity
        for m in re.finditer(r'^##\s+(.+)', raw, re.MULTILINE):
            heading_text = m.group(1).strip()
            heading_set = find_entities(heading_text) | find_bold_entities(
                f'**{heading_text}**')
            file_set |= heading_set

        file_entities[short_name] = file_set
        for eid in file_set:
            if eid not in nodes:
                nodes[eid] = ENTITY_TYPE.get(eid, 'unknown')

        # ── Split into sections by ## headings ────────────
        # Strategy: split on lines that start with ##
        # Each "section" = the heading line + body until next ##
        parts = re.split(r'(?=^## )', raw, flags=re.MULTILINE)
        for part in parts:
            lines = part.split('\n')

            # Entity set for the whole section
            sec_set = find_entities(part) | find_bold_entities(part)

            #  weight=3  — same section (use max with line weights below)
            _apply_edges(sec_set, 3, edge_weights)

            #  weight=5  — same line
            for line in lines:
                line_set = find_entities(line) | find_bold_entities(line)
                _apply_edges(line_set, 5, edge_weights)

        # ── weight=1  — same file  (only for pairs not already captured) ──
        _apply_edges(file_set, 1, edge_weights, only_if_missing=True)

    # ── Build output structures ──────────────────────────
    node_list = []
    for nid in sorted(nodes.keys()):
        label = ENTITY_LABELS.get(nid, nid.replace('-', ' ').title())
        node_list.append({
            'id': nid,
            'type': nodes[nid],
            'label': label,
        })

    edge_list = []
    for (src, tgt, rel), weight in sorted(edge_weights.items()):
        edge_list.append({
            'source': src,
            'target': tgt,
            'relation': rel,
            'weight': weight,
        })
    edge_list.sort(key=lambda e: (-e['weight'], e['source'], e['target']))

    return {
        'version': 1,
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'nodes': node_list,
        'edges': edge_list,
    }


def _apply_edges(entity_set, weight, edge_weights, only_if_missing=False):
    """For every unordered pair in *entity_set*, compute the directed edge
       and bump its weight to at least *weight*."""
    items = sorted(entity_set)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]

            # Determine direction by type hierarchy
            src, tgt = _order_by_type(a, b)
            rel = infer_relation(src, tgt)

            key = (src, tgt, rel)
            if only_if_missing:
                if key not in edge_weights:
                    edge_weights[key] = weight
            else:
                if key not in edge_weights:
                    edge_weights[key] = weight
                elif edge_weights[key] < weight:
                    edge_weights[key] = weight


# Type ordering for edge direction: person > project > technology > concept
_TYPE_ORDER = {'person': 0, 'project': 1, 'technology': 2, 'concept': 3, 'unknown': 9}

def _order_by_type(a, b):
    """Return (source, target) so source has the lower type-order number."""
    oa = _TYPE_ORDER.get(ENTITY_TYPE.get(a, 'unknown'), 9)
    ob = _TYPE_ORDER.get(ENTITY_TYPE.get(b, 'unknown'), 9)
    if oa <= ob:
        return (a, b)
    return (b, a)


# ══════════════════════════════════════════════════════════════════════
#  Commands
# ══════════════════════════════════════════════════════════════════════

def load_graph():
    if not os.path.isfile(GRAPH_FILE):
        return None
    try:
        with open(GRAPH_FILE, 'r') as fh:
            g = json.load(fh)
        return g
    except Exception:
        return None


def cmd_rebuild():
    print('🔍 Scanning memory files...')
    graph = scan()
    with open(GRAPH_FILE, 'w') as fh:
        json.dump(graph, fh, indent=2, ensure_ascii=False)
    print(f'✅ Knowledge graph rebuilt: {len(graph["nodes"])} nodes, '
          f'{len(graph["edges"])} edges')
    print(f'   Saved → {GRAPH_FILE}')


def cmd_stats():
    g = load_graph()
    if not g:
        print('❌ No graph found. Run --rebuild first.')
        sys.exit(1)

    type_counts = {}
    rel_counts = {}
    for n in g['nodes']:
        type_counts[n['type']] = type_counts.get(n['type'], 0) + 1
    for e in g['edges']:
        rel_counts[e['relation']] = rel_counts.get(e['relation'], 0) + 1

    print('📊 Knowledge Graph Statistics')
    print('=' * 40)
    print(f'  Updated : {g["updated"]}')
    print(f'  Nodes   : {len(g["nodes"])}')
    for t in ['person', 'project', 'technology', 'concept']:
        if t in type_counts:
            print(f'    {TYPE_EMOJI.get(t, "❓")} {t:12s} {type_counts[t]}')
    for t, c in sorted(type_counts.items()):
        if t not in ('person', 'project', 'technology', 'concept'):
            print(f'    ❓ {t:12s} {c}')
    print(f'  Edges   : {len(g["edges"])}')
    for r, c in sorted(rel_counts.items()):
        print(f'    🔗 {r:12s} {c}')


def cmd_query(name):
    g = load_graph()
    if not g:
        print('❌ No graph found. Run --rebuild first.')
        sys.exit(1)

    # Resolve name → entity id (try label, then id, then alias)
    entity_id = None
    search = name.lower()

    # 1) Exact id match
    if search in ENTITY_TYPE:
        entity_id = search
    # 2) Alias match
    if not entity_id:
        for alias_lower, eid in ALIAS_TO_ID.items():
            if search == alias_lower:
                entity_id = eid
                break
    # 3) Substring match on label
    if not entity_id:
        for n in g['nodes']:
            if search in n['label'].lower():
                entity_id = n['id']
                break
    # 4) Substring match on id
    if not entity_id:
        for n in g['nodes']:
            if search in n['id'].lower():
                entity_id = n['id']
                break

    if not entity_id:
        print(f'❌ Entity not found: "{name}"')
        # Show suggestions
        print('   Try one of:')
        for n in sorted(g['nodes'], key=lambda x: x['label']):
            print(f'     {n["label"]}  [{n["type"]}]')
        sys.exit(1)

    node = next((n for n in g['nodes'] if n['id'] == entity_id), None)
    if not node:
        print(f'❌ Node "{entity_id}" not in current graph.')
        sys.exit(1)

    print(f'\n🔍 Connections for: {node["label"]}  [{node["type"]}]')
    print('=' * 55)

    conns = [e for e in g['edges']
             if e['source'] == entity_id or e['target'] == entity_id]
    if not conns:
        print('  (no connections found)')
        return

    for e in sorted(conns, key=lambda x: -x['weight']):
        outbound = (e['source'] == entity_id)
        other_id = e['target'] if outbound else e['source']
        other_node = next((n for n in g['nodes'] if n['id'] == other_id), None)
        other_label = other_node['label'] if other_node else other_id

        bar = '█' * e['weight']
        if outbound:
            line = f'  {node["label"]}  ──[{e["relation"]}]──▶  {other_label}'
        else:
            line = f'  {other_label}  ──[{e["relation"]}]──▶  {node["label"]}'
        print(f'{line}  [{bar}] w={e["weight"]}')


def cmd_graph():
    g = load_graph()
    if not g:
        print('❌ No graph found. Run --rebuild first.')
        sys.exit(1)

    print(f'🗺  Knowledge Graph  —  {g["updated"]}')
    print(f'{"=" * 55}')

    print(f'\n📦 NODES ({len(g["nodes"])}):')
    for n in g['nodes']:
        e = TYPE_EMOJI.get(n['type'], '❓')
        print(f'  {e} [{n["type"]:12s}] {n["label"]}')

    print(f'\n🔗 EDGES ({len(g["edges"])}):')
    for e in g['edges']:
        _print_edge(e, g['nodes'])


def _print_edge(e, nodes):
    src = _find_label(e['source'], nodes)
    tgt = _find_label(e['target'], nodes)
    rel = REL_LABELS.get(e['relation'], e['relation'])
    bar = '█' * e['weight']
    print(f'  {src}  ──[{rel}]──▶  {tgt}  [{bar}] w={e["weight"]}')


def _find_label(eid, nodes):
    for n in nodes:
        if n['id'] == eid:
            return n['label']
    return eid


# ══════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        # Quick status
        g = load_graph()
        print('🧠 Knowledge Graph — Quick Status')
        print('=' * 40)
        if g:
            print(f'  ✅ Graph exists : {len(g["nodes"])} nodes, '
                  f'{len(g["edges"])} edges')
            print(f'  📅 Updated      : {g["updated"]}')
            print(f'  💡 Use --rebuild / --stats / --query <name> / --graph')
        else:
            print('  ❌ No graph found. Run with --rebuild to create.')
        return

    cmd = sys.argv[1]

    if cmd == '--rebuild':
        cmd_rebuild()
    elif cmd == '--stats':
        cmd_stats()
    elif cmd == '--query':
        if len(sys.argv) < 3:
            print('Usage: knowledge_graph.py --query <entity>')
            sys.exit(1)
        cmd_query(sys.argv[2])
    elif cmd == '--graph':
        cmd_graph()
    else:
        print(f'Unknown command: {cmd}')
        print('Commands: --rebuild | --stats | --query <name> | --graph')
        sys.exit(1)


if __name__ == '__main__':
    main()
