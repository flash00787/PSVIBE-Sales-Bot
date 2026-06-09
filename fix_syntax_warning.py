with open('/root/psvibe_api_server/app.py', 'r') as f:
    s = f.read()

# Fix the SyntaxWarning - use single quotes properly
s = s.replace("today\\s Confirmed", "today's Confirmed")

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(s)

# Verify
import py_compile
try:
    py_compile.compile('/root/psvibe_api_server/app.py', doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print(f"Syntax Error: {e}")
