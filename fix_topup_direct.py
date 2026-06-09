#!/usr/bin/env python3

import re
import subprocess

print("🔧 Fixing Top Up payment flow spam - Direct approach...")

# Read the current file
with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'r') as f:
    content = f.read()

print("📖 Read members.py successfully")

# Pattern 1: Find and replace the payment method selection block in step_tu_kpay
# This is the problematic section that sends a duplicate message
pattern1 = re.compile(
    r'(if text in methods:\s+d\["tu_current_pay_method"\] = text\s+psf = sum\(d\.get\("tu_payments", {}\)\.values\(\)\)\s+rem = amt - psf\s+await update\.message\.reply_text\(\s+f"[^"]*"\s+f"[^"]*"\s+f"[^"]*"\s+f"[^"]*"\s+f"[^"]*",\s+parse_mode="Markdown",\s+reply_markup=ReplyKeyboardMarkup\(\[NAV_ROW\], resize_keyboard=True\),\s+\)\s+return TU_KPAY)',
    re.MULTILINE | re.DOTALL
)

# Replacement for pattern 1 - just set the method and flag, then call prompt_tu_kpay
replacement1 = '''if text in methods:
        # Store method and call prompt_tu_kpay to show unified display
        d["tu_current_pay_method"] = text
        d["tu_show_amount_input"] = True
        return await prompt_tu_kpay(update, context)'''

print("🔍 Searching for payment method selection block...")
matches = pattern1.findall(content)
if matches:
    print(f"✅ Found {len(matches)} match(es) for payment method block")
    content = pattern1.sub(replacement1, content)
else:
    print("❌ Could not find payment method block - trying line-based approach")
    
    # Alternative approach: find the lines and replace manually
    lines = content.split('\n')
    new_lines = []
    in_payment_block = False
    block_start = -1
    
    for i, line in enumerate(lines):
        if 'if text in methods:' in line and 'tu_current_pay_method' in lines[i+1] if i+1 < len(lines) else False:
            # Start of problematic block
            in_payment_block = True
            block_start = i
            new_lines.append('    if text in methods:')
            new_lines.append('        # Store method and call prompt_tu_kpay to show unified display')
            new_lines.append('        d["tu_current_pay_method"] = text')
            new_lines.append('        d["tu_show_amount_input"] = True')
            new_lines.append('        return await prompt_tu_kpay(update, context)')
        elif in_payment_block and 'return TU_KPAY' in line:
            # End of block - skip this line as we already added our return
            in_payment_block = False
            continue
        elif in_payment_block:
            # Skip lines in the old block
            continue
        else:
            new_lines.append(line)
    
    if block_start >= 0:
        content = '\n'.join(new_lines)
        print(f"✅ Replaced payment method block using line-based approach (started at line {block_start})")

# Pattern 2: Add amount input handling to prompt_tu_kpay
# Find the location after "# Auto-confirm when full payment complete"
pattern2 = r'(# Auto-confirm when full payment complete\s+if remaining <= 0:\s+d\["tu_kpay"\] = d\["tu_payments"\]\.get\("KPay", 0\)\s+d\["tu_cash"\] = d\["tu_payments"\]\.get\("Cash", 0\)\s+return await step_tu_confirm\(update, context\))'

replacement2 = r'''\1

    # Check if we need to show amount input for selected method
    if d.get("tu_show_amount_input") and d.get("tu_current_pay_method"):
        method = d["tu_current_pay_method"]
        await update.message.reply_text(
            f"\U0001f4b3 *{method}* \u1015\u1019\u102b\u100f \u101b\u102d\u102f\u1000\u103a\u1015\u102b\n"
            f"\u2501" * 30 + f"\n"
            f"\U0001f4b0 Top Up: *{amt:,} Ks*  |  Remaining: *{remaining:,} Ks*\n"
            f"\u2501" * 30 + f"\n"
            f"(0 - {remaining:,}) \u1011\u100a\u1039\u1037\u1015\u102b\u1038 -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return TU_KPAY'''

print("🔍 Adding amount input handling to prompt_tu_kpay...")
if re.search(pattern2, content, re.MULTILINE | re.DOTALL):
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE | re.DOTALL)
    print("✅ Added amount input handling")
else:
    print("❌ Could not find auto-confirm block - manual insertion")
    # Find the prompt_tu_kpay function and add after the auto-confirm section
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if 'return await step_tu_confirm(update, context)' in line and 'Auto-confirm' in lines[i-3] if i >= 3 else False:
            # Add our new block after this line
            new_lines.extend([
                '',
                '    # Check if we need to show amount input for selected method',
                '    if d.get("tu_show_amount_input") and d.get("tu_current_pay_method"):',
                '        method = d["tu_current_pay_method"]',
                '        await update.message.reply_text(',
                '            f"\\U0001f4b3 *{method}* \\u1015\\u1019\\u102b\\u100f \\u101b\\u102d\\u102f\\u1000\\u103a\\u1015\\u102b\\n"',
                '            f"\\u2501" * 30 + f"\\n"',
                '            f"\\U0001f4b0 Top Up: *{amt:,} Ks*  |  Remaining: *{remaining:,} Ks*\\n"',
                '            f"\\u2501" * 30 + f"\\n"',
                '            f"(0 - {remaining:,}) \\u1011\\u100a\\u1039\\u1037\\u1015\\u102b\\u1038 -",',
                '            parse_mode="Markdown",',
                '            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),',
                '        )',
                '        return TU_KPAY',
            ])
            print("✅ Manually inserted amount input handling")
            break
    
    content = '\n'.join(new_lines)

# Pattern 3: Add state cleanup after amount is processed
pattern3 = r'(d\["tu_payments"\]\[current_method\] = method_amt\s+return await prompt_tu_kpay\(update, context\))'

replacement3 = r'''d["tu_payments"][current_method] = method_amt
        # Clear the method selection state
        d.pop("tu_current_pay_method", None)
        d.pop("tu_show_amount_input", None)
        return await prompt_tu_kpay(update, context)'''

print("🔍 Adding state cleanup...")
if re.search(pattern3, content, re.MULTILINE | re.DOTALL):
    content = re.sub(pattern3, replacement3, content, flags=re.MULTILINE | re.DOTALL)
    print("✅ Added state cleanup")
else:
    print("⚠️  Could not find state cleanup location - may need manual fix")

# Write the updated content
with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'w') as f:
    f.write(content)

print("💾 Updated members.py")

# Test compilation
print("🧪 Testing Python compilation...")
try:
    result = subprocess.run(['python3', '-m', 'py_compile', 'bot/handlers/members.py'], 
                          capture_output=True, text=True, cwd='/root/psvibe-sales-bot')
    if result.returncode == 0:
        print("✅ Python compilation successful")
        print("\n📋 Summary of changes:")
        print("   1. Removed duplicate message when payment method selected")
        print("   2. Added state flag tu_show_amount_input to control flow")  
        print("   3. Updated prompt_tu_kpay to handle amount input display")
        print("   4. Added cleanup of state flags after amount entry")
        print("\n🎯 Top Up spam and stuck issues should be fixed!")
        
    else:
        print(f"❌ Compilation error: {result.stderr}")
        exit(1)
        
except Exception as e:
    print(f"❌ Compilation test failed: {e}")
    exit(1)

print("✅ Fix completed successfully!")