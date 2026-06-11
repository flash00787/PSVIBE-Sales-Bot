#!/usr/bin/env python3
"""Add Kora dashboard route to app.py"""
import re

with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

kora_route = '''
@app.get("/kora")
@app.get("/kora/{path:path}")
async def serve_kora_dashboard(request: Request, path: str = ""):
    """Serve Kora Dashboard"""
    import os
    kora_file = os.path.join(os.path.dirname(__file__), "..", ".openclaw", "workspace", "kora_dashboard", "index.html")
    if os.path.exists(kora_file):
        with open(kora_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return JSONResponse({"success": False, "error": "Kora Dashboard not found"}, status_code=404)
'''

# Insert before the 404 handler (only once)
if '@app.get("/kora")' not in content:
    content = content.replace(
        '@app.exception_handler(404)',
        kora_route.strip() + '\n\n\n@app.exception_handler(404)'
    )
    with open('/root/psvibe_api_server/app.py', 'w') as f:
        f.write(content)
    print("✅ Kora route added to app.py")
else:
    print("⏭️ Kora route already exists")

# Update Caddyfile
caddy_content = '''{
    admin off
}

:80 {
    handle_path /dashboard/* {
        reverse_proxy host.docker.internal:9090
    }
    handle_path /kora/* {
        reverse_proxy host.docker.internal:8000
    }
    handle /api/* {
        reverse_proxy host.docker.internal:8000
    }
    handle /receipt* {
        reverse_proxy host.docker.internal:8000
    }
    handle /auth/* {
        reverse_proxy host.docker.internal:8000
    }
    handle /n8n/* {
        reverse_proxy host.docker.internal:8000
    }
    handle {
        reverse_proxy host.docker.internal:8000
    }
}

kora.ps-vibe.com {
    reverse_proxy host.docker.internal:9091
}
'''

with open('/root/Aung Chan Myint/Caddyfile', 'w') as f:
    f.write(caddy_content)
print("✅ Caddyfile updated to use port 8000 for /kora/")
