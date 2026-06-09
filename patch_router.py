import re

path = 'src/router/index.ts'
with open(path, 'r') as f:
    content = f.read()

# Backup the original
with open(path + '.bak.router', 'w') as f:
    f.write(content)

# Find the closing of routes array (after games route, before wildcard)
# Add sale-daily and financial-report routes
old_closing = """    {
      path: '/games',
      name: 'games',
      component: () => import('../views/GamesLibrary.vue'),
      meta: { requiresAuth: true, title: 'Games' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },"""

new_closing = """    {
      path: '/games',
      name: 'games',
      component: () => import('../views/GamesLibrary.vue'),
      meta: { requiresAuth: true, title: 'Games' },
    },
    {
      path: '/sales-daily',
      name: 'sales-daily',
      component: () => import('../views/SaleDaily.vue'),
      meta: { requiresAuth: true, title: 'Sales Daily' },
    },
    {
      path: '/financial-report',
      name: 'financial-report',
      component: () => import('../views/FinancialReport.vue'),
      meta: { requiresAuth: true, title: 'Financial Report' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },"""

if old_closing in content:
    content = content.replace(old_closing, new_closing)
    with open(path, 'w') as f:
        f.write(content)
    print('Router updated with SaleDaily + FinancialReport routes')
else:
    print('Pattern not found, searching...')
    if '/games' in content and 'GamesLibrary' in content:
        print('Games route found but pattern mismatch')
print('Route count:', content.count("path:"))
