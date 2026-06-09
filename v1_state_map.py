# Phase 2: Map V.1 ConversationHandler states to actual entry points
# V.1 uses ConversationHandler with states dict - each state has CallbackQueryHandlers
# We need to find what STATE each button press maps to

with open('/root/Sales-Tele-Bot/main.py.bak.phase4') as f:
    v1_text = f.read()

# Find ConversationHandler definition
import re

# Find all state names used in ConversationHandler
states_found = set()
for m in re.finditer(r'(\w+)\s*:\s*\[', v1_text):
    if m.group(1).isupper():
        states_found.add(m.group(1))

# Find all pattern='...' in CallbackQueryHandlers within states
print('=== V.1 STATES and their callback patterns ===')
# Find ConversationHandler block
ch_match = re.search(r'conv_handler\s*=\s*ConversationHandler\(', v1_text)
if ch_match:
    start = ch_match.start()
    # Find matching closing paren
    depth = 1
    i = start
    while depth > 0 and i < len(v1_text):
        i += 1
        if v1_text[i] == '(':
            depth += 1
        elif v1_text[i] == ')':
            depth -= 1
    
    ch_block = v1_text[start:i+1]
    
    # Extract entry points
    entry_match = re.search(r'entry_points\s*=\s*\[(.*?)\]', ch_block, re.DOTALL)
    if entry_match:
        print('Entry points:')
        print(entry_match.group(1)[:200])
    
    # Extract fallbacks
    fallback_match = re.search(r'fallbacks\s*=\s*\[(.*?)\]', ch_block, re.DOTALL)
    if fallback_match:
        print('Fallbacks:')
        print(fallback_match.group(1)[:200])
    
    # Extract states
    states_match = re.search(r'states\s*=\s*\{(.*?)\}', ch_block, re.DOTALL)
    if states_match:
        states_block = states_match.group(1)
        # Split by state name
        state_patterns = re.findall(r'(\w+)\s*:\s*\[(.*?)\]', states_block, re.DOTALL)
        for state_name, handlers in state_patterns:
            if state_name.isupper():
                print(f'\nState {state_name}:')
                # Extract callback functions and patterns
                callbacks = re.findall(r'CallbackQueryHandler\((\w+),\s*pattern=(.*?)\)', handlers)
                for func, pat in callbacks:
                    print(f'  {func} -> {pat}')
else:
    print('Could not find ConversationHandler in V.1')
