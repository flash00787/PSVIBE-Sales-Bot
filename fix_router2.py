with open('/root/psvibe-dashboard/src/router/index.ts') as f:
    s = f.read()

# The bad block to replace
old = """    {
      path: "/shareholders",
      name: "shareholders",
      component: () => import("../views/ShareholdersView.vue"),
      meta: { requiresAuth: true, title: Shareholders },
      meta: { requiresAuth: true, title: "Shareholders" },
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },"""

new = """    {
      path: "/shareholders",
      name: "shareholders",
      component: () => import("../views/ShareholdersView.vue"),
      meta: { requiresAuth: true, title: "Shareholders" },
    },"""

s = s.replace(old, new)

with open('/root/psvibe-dashboard/src/router/index.ts', 'w') as f:
    f.write(s)

# Verify
with open('/root/psvibe-dashboard/src/router/index.ts') as f:
    for i, line in enumerate(f.readlines()):
        print(f'{i+1}: {line}', end='')
