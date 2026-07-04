from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.config import APP_NAME, APP_VERSION, API_PREFIX

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# Serve Vue.js frontend static files
STATIC_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static'))

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Import and register routers
from app.routes import auth_routes, product_routes, sale_routes
from app.routes import purchase_routes, customer_routes, supplier_routes
from app.routes import report_routes, settings_routes, payment_accounts

app.include_router(auth_routes.router, prefix=f'{API_PREFIX}/auth', tags=['Auth'])
app.include_router(product_routes.router, prefix=f'{API_PREFIX}/products', tags=['Products'])
app.include_router(sale_routes.router, prefix=f'{API_PREFIX}/sales', tags=['Sales'])
app.include_router(purchase_routes.router, prefix=f'{API_PREFIX}/purchases', tags=['Purchases'])
app.include_router(customer_routes.router, prefix=f'{API_PREFIX}/customers', tags=['Customers'])
app.include_router(supplier_routes.router, prefix=f'{API_PREFIX}/suppliers', tags=['Suppliers'])
app.include_router(report_routes.router, prefix=f'{API_PREFIX}/reports', tags=['Reports'])
app.include_router(settings_routes.router, prefix=f'{API_PREFIX}/settings', tags=['Settings'])
app.include_router(payment_accounts.router, prefix=f'{API_PREFIX}/payment-accounts', tags=['Payment Accounts'])

@app.get(f'{API_PREFIX}/health')
async def health():
    return {'status': 'ok', 'app': APP_NAME, 'version': APP_VERSION}

# Mount static files (JS, CSS, assets) + SPA fallback
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, 'assets')
    if os.path.isdir(assets_dir):
        app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')

    @app.get('/{full_path:path}')
    async def spa_fallback(full_path: str):
        # Don't intercept API routes
        if full_path.startswith('api/'):
            from fastapi import HTTPException
            raise HTTPException(404, 'Not found')
        # Try to serve the requested file from static dir
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # SPA fallback: serve index.html for all other routes
        index_path = os.path.join(STATIC_DIR, 'index.html')
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {'message': 'Frontend not found'}

    # Handle root path explicitly
    @app.get('/')
    async def root():
        index_path = os.path.join(STATIC_DIR, 'index.html')
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {'message': 'AKT Clothing Shop ERP API'}

else:
    @app.get('/')
    async def root():
        return {'message': 'AKT Clothing Shop ERP API', 'version': APP_VERSION}
