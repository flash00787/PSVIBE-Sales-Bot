"""Update Customer Bot AI to use grouped food menu"""
import sys

# === Step 1: Add _fetch_food_menu_grouped() to api.py ===
with open("/root/psvibe-sales-bot/customer_bot/api.py", encoding="utf-8") as f:
    api_py = f.read()

new_fn = """
async def _fetch_food_menu_grouped() -> str:
    \"\"\"Fetch food menu grouped by category via API (5-min cache).\"\"\"
    cached = await _cache_get("food_menu")
    if cached is not None:
        return cached
    try:
        data = await _api_get("fetch_food_menu")
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
        elif isinstance(data, list):
            items = data
        else:
            return ""
        lines = []
        for cat in items:
            cat_name = cat.get("category", "")
            cat_emoji = cat.get("emoji", "")
            cat_items = cat.get("items", [])
            if not cat_items:
                continue
            header = f"{cat_emoji} {cat_name}:" if cat_emoji else f"** {cat_name} **"
            lines.append(header)
            for item in cat_items:
                name = item.get("name", "").strip()
                price = item.get("price")
                if name and price:
                    lines.append(f"  - {name}: {int(price):,} Ks")
            lines.append("")
        result = "\\n".join(lines).strip()
        if result:
            await _cache_set("food_menu", result, ttl=300)
        return result
    except Exception as e:
        logging.warning("fetch_food_menu_grouped failed: %s", e)
        return ""
"""

# Insert before the last function definition
insert_point = api_py.rfind("async def ")
insert_line = api_py.rfind("\\n", 0, insert_point)
api_py = api_py[:insert_line] + new_fn + api_py[insert_line:]

with open("/root/psvibe-sales-bot/customer_bot/api.py", "w", encoding="utf-8") as f:
    f.write(api_py)
import ast
ast.parse(api_py)
print("Step 1: api.py UPDATED with _fetch_food_menu_grouped()")

# === Step 2: Update prompts.py ===
with open("/root/psvibe-sales-bot/customer_bot/data/prompts.py", encoding="utf-8") as f:
    prompts_py = f.read()

# Add fetch_food_menu_fn parameter
old_sig = (
    'async def _build_ai_system_prompt(\n'
    '    priority_care: bool = False,\n'
    '    fetch_config_fn=None,\n'
    '    build_rate_lines_fn=None,\n'
    '    build_bonus_table_fn=None,\n'
    '    fetch_games_full_fn=None,\n'
    '    build_live_game_library_fn=None,\n'
    '    btc_contact: str = "",\n'
    '    btn_games: str = "",\n'
    ') -> str:'
)
new_sig = (
    'async def _build_ai_system_prompt(\n'
    '    priority_care: bool = False,\n'
    '    fetch_config_fn=None,\n'
    '    build_rate_lines_fn=None,\n'
    '    build_bonus_table_fn=None,\n'
    '    fetch_games_full_fn=None,\n'
    '    build_live_game_library_fn=None,\n'
    '    fetch_food_menu_fn=None,\n'
    '    btc_contact: str = "",\n'
    '    btn_games: str = "",\n'
    ') -> str:'
)

prompts_py = prompts_py.replace(old_sig, new_sig)

# Replace food_text block to use grouped menu
old_food = (
    '    if food_prices:\n'
    '        food_text = "".join(\n'
    '            f"   {name} \\u2014 {int(price):,} Ks"\n'
    '            for name, price in food_prices.items()\n'
    '            if name and price\n'
    '        )\n'
    '    else:\n'
    '        food_text = "(Menu available at the lounge)"'
)

# Can't do exact match because of encoding, let me find by context
# Find the food section by looking for the pattern
import re
pattern = re.compile(
    r'if food_prices:\s*\n'
    r'\s+food_text = .*?\n'
    r'(\s+for name, price in food_prices\.items\(\)\s*\n'
    r'\s+if name and price\s*\n'
    r'\s+\)\s*\n)?'
    r'\s+else:\s*\n'
    r'\s+food_text = "\(Menu available at the lounge\)"',
    re.DOTALL
)

# Simpler approach - just do the replacement with specific strings
old_food_block = (
    "    if food_prices:\n"
    '        food_text = "".join(\n'
    '            f"   {name} \\u2014 {int(price):,} Ks"\n'
    "            for name, price in food_prices.items()\n"
    "            if name and price\n"
    "        )\n"
    "    else:\n"
    '        food_text = "(Menu available at the lounge)"'
)

new_food_block = (
    "    food_menu_text = await fetch_food_menu_fn() if fetch_food_menu_fn else \"\"\n"
    "    if not food_menu_text and food_prices:\n"
    '        food_text = "".join(\n'
    '            f"   {name} \\u2014 {int(price):,} Ks"\n'
    "            for name, price in food_prices.items()\n"
    "            if name and price\n"
    "        )\n"
    "    elif food_menu_text:\n"
    "        food_text = food_menu_text\n"
    "    else:\n"
    '        food_text = "(Menu available at the lounge)"'
)

# Use raw comparison to handle encoding
old_food_simple = "    if food_prices:"
new_food_simple = "    food_menu_text = await fetch_food_menu_fn() if fetch_food_menu_fn else \"\"\n    if food_menu_text:\n        food_text = food_menu_text\n    elif food_prices:"

# Find the exact string in the file
with open("/root/psvibe-sales-bot/customer_bot/data/prompts.py", "rb") as f:
    raw = f.read()
    
# Search for the old pattern
old_bytes = b"    if food_prices:"
if old_bytes in raw:
    print("Found food_prices block")
    # Read the lines around it
    lines = open("/root/psvibe-sales-bot/customer_bot/data/prompts.py", encoding="utf-8").readlines()
    for i, line in enumerate(lines):
        if "if food_prices:" in line:
            print(f"  Line {i+1}: {line.rstrip()}")
            # Print next few lines
            for j in range(i, min(i+8, len(lines))):
                print(f"    {j+1}: {lines[j].rstrip()}")
else:
    print("food_prices pattern not found in raw")
    
print("\\n=== Done ===")
