with open('/root/Sales-Tele-Bot/main.py.bak.phase4') as f:
    v1_text = f.read()

idx = v1_text.index('ConversationHandler(')
depth = 1
i = idx + len('ConversationHandler(')
while depth > 0 and i < len(v1_text):
    if v1_text[i] == '(':
        depth += 1
    elif v1_text[i] == ')':
        depth -= 1
    i += 1

ch_text = v1_text[idx:i]

# Extract all state -> handler mappings
import re

states_block = re.search(r'states\s*=\s*\{(.*?)\}', ch_text, re.DOTALL)
if states_block:
    # Parse each state
    state_text = states_block.group(1)
    # Find state names (uppercase with underscores)
    state_pattern = re.findall(r'(\w+)\s*:\s*\[(.*?)\]', state_text, re.DOTALL)
    print('=== ALL V.1 STATES & HANDLERS ===')
    for state_name, handlers in state_pattern:
        if state_name.isupper():
            # Extract handler info
            handlers_clean = handlers.replace('\n', ' ').strip()
            handler_types = re.findall(r'(\w+)\(', handlers_clean)
            handler_funcs = re.findall(r'\w+\(([^,)]+)', handlers_clean)
            print(f'\nState {state_name}:')
            for htype, hfunc in zip(handler_types, handler_funcs):
                print(f'  {htype}({hfunc})')

# Also get entry points
entry = re.search(r'entry_points\s*=\s*\[(.*?)\]', ch_text, re.DOTALL)
if entry:
    print('\n\n=== ENTRY POINTS ===')
    entries = re.findall(r'(\w+)\(["\'](\w+)["\'],?\s*(\w+)\)', entry.group(1))
    for htype, cmd, func in entries:
        print(f'  CommandHandler("{cmd}" → {func})')
    remaining = re.findall(r'(\w+)\(([^)]+)\)', entry.group(1))
    for r in remaining:
        if 'CommandHandler' not in r[0]:
            print(f'  {r[0]}({r[1]})')
