# Fix: Remove pytz dependency from handlers/__init__.py
# Use datetime's timezone implementation instead

path = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(path) as f:
    content = f.read()

# Replace pytz import with datetime.timezone
content = content.replace("import pytz", "import datetime as _dt")

# Replace now_mmt implementation
old_now_mmt = '''def now_mmt():
    """Get current time in Asia/Yangon timezone (UTC+6:30)."""
    return datetime.datetime.now(pytz.timezone('Asia/Yangon')).strftime('%H:%M')'''

new_now_mmt = '''def now_mmt():
    """Get current time in Asia/Yangon timezone (UTC+6:30)."""
    # UTC+6:30 for Myanmar
    return (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=6, minutes=30)).strftime('%H:%M')'''

content = content.replace(old_now_mmt, new_now_mmt)

with open(path, 'w') as f:
    f.write(content)

print('DONE: Removed pytz dependency from handlers/__init__.py')
print('now_mmt() now uses datetime.timezone.utc + timedelta')

# Verify no more pytz references
if 'pytz' in content:
    print('WARNING: pytz still referenced!')
else:
    print('✅ No pytz references remain')
