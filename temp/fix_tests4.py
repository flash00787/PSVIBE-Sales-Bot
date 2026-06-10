#!/usr/bin/env python3
"""Final fix for conftest mock bot: handle async names + submodules"""
import re

with open('/root/psvibe-sales-bot/tests/conftest.py', 'r') as f:
    content = f.read()

# Fix 1: Update __getattr__ to return AsyncMock for _async names
old_getattr = '''    def _mock_getattr(name):
        if name.startswith('_'):
            raise AttributeError(name)
        mock = MagicMock()
        setattr(bot, name, mock)
        return mock'''

new_getattr = '''    def _mock_getattr(name):
        if name.startswith('_') and not name.startswith('_replit'):
            raise AttributeError(name)
        if name.endswith('_async') or name.startswith('_replit'):
            mock = AsyncMock()
        elif name.startswith(('cmd_', 'show_', 'prompt_', 'step_')):
            mock = AsyncMock()
        else:
            mock = MagicMock()
        setattr(bot, name, mock)
        return mock'''

if old_getattr in content:
    content = content.replace(old_getattr, new_getattr)
    print('Updated __getattr__ for async names')
else:
    print('__getattr__ pattern not found')

# Fix 2: Add bot.handlers submodules (console, games, etc.)
# Find where bot.handlers is created and add submodules
old_handlers = '''_handlers = types.ModuleType('bot.handlers')
_handlers.__package__ = 'bot.handlers'
_handlers.__path__ = [os.path.join(_BOT_DIR, 'handlers')]
_handlers.__file__ = os.path.join(_BOT_DIR, 'handlers', '__init__.py')
sys.modules['bot.handlers'] = _handlers'''

if old_handlers in content:
    new_handlers = old_handlers + '''

# Register handler submodules so patch() works (e.g., patch('bot.handlers.console.show_console_menu'))
_handler_modules = ['console', 'games', 'members', 'reports', 'finance', 'main_menu', 'booking', 'notify', 'sales', 'food', 'inventory', 'discount', 'booking_flow', 'console_management', 'console_mgmt', 'finance_menu', 'game_library']
for _hm in _handler_modules:
    _m = types.ModuleType(f'bot.handlers.{_hm}')
    _m.__package__ = f'bot.handlers.{_hm}'
    _m.__file__ = os.path.join(_BOT_DIR, 'handlers', f'{_hm}.py')
    sys.modules[f'bot.handlers.{_hm}'] = _m'''
    
    content = content.replace(old_handlers, new_handlers)
    print('Added handler submodules')
else:
    print('handlers pattern not found')

with open('/root/psvibe-sales-bot/tests/conftest.py', 'w') as f:
    f.write(content)
print('conftest.py: UPDATED v3')
