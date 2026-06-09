#!/usr/bin/env python3
"""Add shareholders route + nav item."""
# 1. Route
with open('/root/psvibe-dashboard/src/router/index.ts') as f:
    s = f.read()

route = '''    {
      path: '/shareholders',
      name: 'shareholders',
      component: () => import('../views/ShareholdersView.vue'),
      meta: { requiresAuth: true, title: 'Shareholders' },
    },
'''
idx = s.find("{ path: '/:pathMatch(.*)*'")
s = s[:idx] + route + s[idx:]

with open('/root/psvibe-dashboard/src/router/index.ts', 'w') as f:
    f.write(s)
print('Route added')

# 2. Nav
with open('/root/psvibe-dashboard/src/components/AppLayout.vue') as f:
    s = f.read()

nav = "  { path: '/shareholders', label: 'Shareholders', icon: '\U0001f3e6' },\n    "
idx = s.find("{ path: '/finance', label: 'Web Finance'")
s = s[:idx] + nav + s[idx:]

with open('/root/psvibe-dashboard/src/components/AppLayout.vue', 'w') as f:
    f.write(s)
print('Nav item added')
