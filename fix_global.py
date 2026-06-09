with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    content = f.read()

# Fix: move global _MBR_TS to top of save_referral_code function
old_func_start = 'def save_referral_code(member_id: str, code: str) -> bool:\n    """Write referral code to Card_Wallet col Q (1-based col 17) for the given member. Returns True on success."""\n    if _HAS_API:'
new_func_start = 'def save_referral_code(member_id: str, code: str) -> bool:\n    """Write referral code to Card_Wallet col Q (1-based col 17) for the given member. Returns True on success."""\n    global _MBR_TS\n    if _HAS_API:'

if old_func_start not in content:
    print("FIX3_FAIL: func start not found")
    import sys; sys.exit(1)

content = content.replace(old_func_start, new_func_start)

# Remove first inner redundant global
old1 = '        if result is not None:\n            global _MBR_TS\n            _MBR_TS = 0.0'
new1 = '        if result is not None:\n            _MBR_TS = 0.0'
content = content.replace(old1, new1)

# Remove second inner redundant global
old2 = '                global _MBR_TS\n                _MBR_TS = 0.0  # invalidate cache'
new2 = '                _MBR_TS = 0.0  # invalidate cache'
content = content.replace(old2, new2)

with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.write(content)

print("FIX3_OK")
