with open('/root/psvibe_api_server/app.py') as f:
    s = f.read()

# Fix: add parameter to the MAX(id) query
import re
# Find the broken call
old = '_mysql_query_one("SELECT MAX(id) as id FROM console_booking WHERE console_id=%s")'
new = '_mysql_query_one("SELECT MAX(id) as id FROM console_booking WHERE console_id=%s", (console_id,))'
s = s.replace(old, new)

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(s)

import py_compile
try:
    py_compile.compile('/root/psvibe_api_server/app.py', doraise=True)
    print('Syntax OK')
except py_compile.PyCompileError as e:
    print('Error:', e)
