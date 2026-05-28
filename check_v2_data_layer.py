# V.2 Data Flow Analysis: What does V.2 use for data?
# Check API calls patterns in handler files  

import os, re

handlers_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'
bot_dir = '/root/Sales-Tele-Bot_refactored/bot'

# Pattern 1: Replit API calls
replit_patterns = [r'_replit_get', r'_replit_post', r'_replit_patch', r'_replit_', r'Replit']

# Pattern 2: gspread/Google Sheets direct
gspread_patterns = [r'gspread', r'gc\.open', r'sheet\.', r'worksheet', r'gspread', r'Google Sheets', r'sheets\.google']

# Pattern 3: SQLite / asyncpg / database
db_patterns = [r'sqlite', r'asyncpg', r'psycopg', r'db\.', r'database', r'psvibe\.db', r'sync_sheets']

# Pattern 4: requests/urllib/aiohttp API calls
api_patterns = [r'aiohttp', r'requests\.', r'urllib', r'httpx', r'curl_cffi']

# Pattern 5: Replit DB (from V.1)
replit_db = [r'Replit', r'replit', r'REPLIT']

results = {k: 0 for k in ['replit_api', 'gspread', 'sqlite_db', 'http_api', 'replit_db']}

for fname in sorted(os.listdir(handlers_dir)):
    if not fname.endswith('.py'):
        continue
    fpath = os.path.join(handlers_dir, fname)
    with open(fpath) as f:
        content = f.read()
    
    if any(re.search(p, content, re.IGNORECASE) for p in replit_patterns):
        results['replit_api'] += 1
    
    if any(re.search(p, content, re.IGNORECASE) for p in gspread_patterns):
        results['gspread'] += 1
    
    if any(re.search(p, content, re.IGNORECASE) for p in db_patterns):
        results['sqlite_db'] += 1
    
    if any(re.search(p, content, re.IGNORECASE) for p in api_patterns):
        results['http_api'] += 1
    
    if any(re.search(p, content, re.IGNORECASE) for p in replit_db):
        results['replit_db'] += 1

print('=== V.2 Data Access Patterns (handler files) ===')
for k, v in results.items():
    print(f'  {k:15s}: {v} files')

# Check __init__.py for what it uses
init_path = os.path.join(bot_dir, '__init__.py')
with open(init_path) as f:
    init_content = f.read()

print('\n=== bot/__init__.py Data Access ===')
for k, patterns in [('Replit API', replit_patterns), ('gspread', gspread_patterns),
                     ('SQLite', db_patterns), ('requests/urllib', api_patterns)]:
    if any(re.search(p, init_content, re.IGNORECASE) for p in patterns):
        print(f'  {k}: YES')
    else:
        print(f'  {k}: NO')

# Check main.py (app entry)
main_path = os.path.join(bot_dir, 'app.py')
with open(main_path) as f:
    main_content = f.read()
print('\n=== app.py Data Access ===')
for k, patterns in [('Replit API', replit_patterns), ('gspread', gspread_patterns),
                     ('SQLite', db_patterns)]:
    if any(re.search(p, main_content, re.IGNORECASE) for p in patterns):
        print(f'  {k}: YES')
    else:
        print(f'  {k}: NO')
