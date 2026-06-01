#!/usr/bin/env python3

import subprocess

# The key fix: Remove the duplicate reply_text call in step_tu_kpay
# when a payment method is selected, and instead set a flag and
# call prompt_tu_kpay immediately

print("🔧 Fixing Top Up payment flow spam issue...")

# Step 1: Remove the problematic reply_text block when payment method is selected
# Lines approximately 1154-1163 in step_tu_kpay
cmd1 = """
sed -i '/d\["tu_current_pay_method"\] = text/,/return TU_KPAY/{
/await update\.message\.reply_text(/,/)/d
/return TU_KPAY/c\
        # Store method and call prompt_tu_kpay to show unified display\
        d["tu_current_pay_method"] = text\
        d["tu_show_amount_input"] = True\
        return await prompt_tu_kpay(update, context)
}' /root/psvibe-sales-bot/bot/handlers/members.py
"""

# Step 2: Update prompt_tu_kpay to handle the amount input state
cmd2 = """
sed -i '/# Auto-confirm when full payment complete/a\
\
    # Check if we need to show amount input for selected method\
    if d.get("tu_show_amount_input") and d.get("tu_current_pay_method"):\
        method = d["tu_current_pay_method"]\
        await update.message.reply_text(\
            f"\\\\U0001f4b3 *{method}* \\\\u1015\\\\u1019\\\\u102b\\\\u100f \\\\u101b\\\\u102d\\\\u102f\\\\u1000\\\\u103a\\\\u1015\\\\u102b\\\\n"\
            f"\\\\u2501" * 30 + f"\\\\n"\
            f"\\\\U0001f4b0 Top Up: *{amt:,} Ks*  |  Remaining: *{remaining:,} Ks*\\\\n"\
            f"\\\\u2501" * 30 + f"\\\\n"\
            f"(0 - {remaining:,}) \\\\u1011\\\\u100a\\\\u1039\\\\u1037\\\\u1015\\\\u102b\\\\u1038 -",\
            parse_mode="Markdown",\
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),\
        )\
        return TU_KPAY
' /root/psvibe-sales-bot/bot/handlers/members.py
"""

# Step 3: Clean up state after amount is entered
cmd3 = """
sed -i '/d\["tu_payments"\]\[current_method\] = method_amt/a\
        # Clear the method selection state\
        d.pop("tu_current_pay_method", None)\
        d.pop("tu_show_amount_input", None)
' /root/psvibe-sales-bot/bot/handlers/members.py
"""

try:
    print("Step 1: Removing duplicate message in payment method selection...")
    subprocess.run(cmd1, shell=True, check=True, cwd='/root/psvibe-sales-bot')
    
    print("Step 2: Adding amount input state handling to prompt_tu_kpay...")
    subprocess.run(cmd2, shell=True, check=True, cwd='/root/psvibe-sales-bot')
    
    print("Step 3: Adding state cleanup after amount entry...")
    subprocess.run(cmd3, shell=True, check=True, cwd='/root/psvibe-sales-bot')
    
    print("✅ Applied all fixes successfully")
    
    # Test compilation
    print("🧪 Testing Python compilation...")
    result = subprocess.run(['python3', '-m', 'py_compile', 'bot/handlers/members.py'], 
                          capture_output=True, text=True, cwd='/root/psvibe-sales-bot')
    if result.returncode == 0:
        print("✅ Python compilation successful")
        
        # Show what changed
        print("\n📋 Summary of changes:")
        print("   1. Removed duplicate message when payment method selected")
        print("   2. Added state flag tu_show_amount_input to control flow")  
        print("   3. Updated prompt_tu_kpay to handle amount input display")
        print("   4. Added cleanup of state flags after amount entry")
        print("\n🎯 This should fix the spam and stuck issues!")
        
    else:
        print(f"❌ Compilation error: {result.stderr}")
        exit(1)
        
except subprocess.CalledProcessError as e:
    print(f"❌ sed command failed: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Fix failed: {e}")
    exit(1)