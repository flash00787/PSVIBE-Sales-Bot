# Check V.2's app.py for ConversationHandler and step functions
# See if V.2 uses MessageHandler or CallbackQueryHandler

v2_app = '/root/Sales-Tele-Bot_refactored/bot/app.py'
with open(v2_app) as f:
    content = f.read()

print('=== V.2 app.py ConversationHandler ===')
import re

# Find ConversationHandler
if 'ConversationHandler(' in content:
    idx = content.index('ConversationHandler(')
    # Extract
    depth = 1
    i = idx + len('ConversationHandler(')
    while depth > 0 and i < len(content):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
        i += 1
    ch_text = content[idx:i]
    print(f'ConversationHandler: {len(ch_text)} chars')
    
    # Find states
    states_match = re.search(r'states\s*=\s*\{(.*?)\}', ch_text, re.DOTALL)
    if states_match:
        state_text = states_match.group(1)
        # Extract handler types per state
        state_handlers = re.findall(r'(\w+)\s*:\s*\[(.*?)\]', state_text, re.DOTALL)
        print(f'\nStates: {len(state_handlers)}')
        for sname, handlers in state_handlers:
            if sname.isupper():
                # Count handler types
                msg_count = handlers.count('MessageHandler')
                cb_count = handlers.count('CallbackQueryHandler')
                cmd_count = handlers.count('CommandHandler')
                print(f'  {sname}: MessageHandler={msg_count}, CallbackQuery={cb_count}, Command={cmd_count}')
                if cb_count > 0:
                    # Show callback handler details
                    cb_funcs = re.findall(r'CallbackQueryHandler\((\w+)', handlers)
                    for func in cb_funcs:
                        print(f'    → {func}')
else:
    print('NO ConversationHandler in V.2 app.py!')

# Also check handlers/__init__.py for conv_handler
h_init = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(h_init) as f:
    h_content = f.read()

if 'conv_handler' in h_content or 'ConversationHandler' in h_content:
    print('\nconv_handler found in handlers/__init__.py')
else:
    print('\nconv_handler NOT in handlers/__init__.py')

# Check main_menu.py for step_main_menu 
mm_path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(mm_path) as f:
    mm_content = f.read()

has_step = 'def step_main_menu' in mm_content
has_show = 'def show_main_menu' in mm_content
print(f'\nmain_menu.py has step_main_menu: {has_step}')
print(f'main_menu.py has show_main_menu: {has_show}')
if not has_step:
    # What functions does it have?
    funcs = re.findall(r'^def (\w+)\(', mm_content, re.MULTILINE)
    print(f'Functions in main_menu.py: {funcs}')
