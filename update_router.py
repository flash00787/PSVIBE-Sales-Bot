# Update router to add dividends route
with open('/root/psvibe-dashboard/src/router/index.ts', 'r') as f:
    content = f.read()

old = '''{ path: "/profit-distribution", name: "profit-distribution", component: () => import("../views/ProfitDistributionView.vue"), meta: { requiresAuth: true, title: "Profit Distribution" } },'''
new = old + "\n    { path: '/dividends', name: 'dividends', component: () => import('../views/DividendsView.vue'), meta: { requiresAuth: true, title: 'Dividends' } },"
content = content.replace(old, new)

with open('/root/psvibe-dashboard/src/router/index.ts', 'w') as f:
    f.write(content)
print('Router updated OK')
