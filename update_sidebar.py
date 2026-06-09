# Update sidebar to add Dividends nav item
with open('/root/psvibe-dashboard/src/components/AppLayout.vue', 'r') as f:
    content = f.read()

old = "      { path: '/profit-distribution', label: 'Profit Dist.'  , icon: '📊' },"
new = old + "\n      { path: '/dividends', label: 'Dividends', icon: '💸' },"
content = content.replace(old, new)

with open('/root/psvibe-dashboard/src/components/AppLayout.vue', 'w') as f:
    f.write(content)
print('Sidebar updated OK')
