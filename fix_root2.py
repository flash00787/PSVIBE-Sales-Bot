import sys

with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

# Check if root route already exists
if '@app.get("/")' in content:
    print("Root route already exists")
    sys.exit(0)

# Find the health route section and insert before it
marker = '''
# ═══════════════════════════════════════
@app.get("/api/health", tags=["System"])'''

insertion = '''
# ═══════════════════════════════════════
#  ROOT HEALTH
@app.get("/", tags=["System"])
async def root_health():
    """Simple health check at the API root."""
    return {"status": "ok", "service": "psvibe-api"}

''' + marker.lstrip('\n')

if marker in content:
    content = content.replace(marker, insertion)
    with open("/root/psvibe_api_server/app.py", "w") as f:
        f.write(content)
    print("Root route added successfully")
else:
    print("Marker not found!")
