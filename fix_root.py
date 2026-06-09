import re

with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

# Fix the mangled line
old = '''@app.get("/", tags=["System"])async def root_health():    return {"status": "ok", "service": "psvibe-api"}'''
new = '''@app.get("/", tags=["System"])
async def root_health():
    return {"status": "ok", "service": "psvibe-api"}'''

if old in content:
    content = content.replace(old, new)
    with open("/root/psvibe_api_server/app.py", "w") as f:
        f.write(content)
    print("Fixed.")
else:
    # Check if it's already clean
    if '@app.get("/", tags=["System"])' in content:
        print("Already OK")
    else:
        print("Root route not found in expected format")
