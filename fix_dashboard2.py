#!/usr/bin/env python3
"""Fix remaining issues in PS VIBE Dashboard pages."""
import paramiko

HOST = "5.223.81.16"
KEY_PATH = "/home/node/.openclaw/workspace/.ssh/id_rsa"
VIEWS_DIR = "/root/psvibe-dashboard/src/views"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
ssh.connect(HOST, username="root", pkey=key, timeout=15)
print("✅ Connected!")

def read_file(path):
    _, stdout, _ = ssh.exec_command(f"cat '{path}'")
    return stdout.read().decode('utf-8', errors='replace')

def write_file(path, content):
    sftp = ssh.open_sftp()
    with sftp.open(path, 'w') as f:
        f.write(content)
    sftp.close()

# ============ Fix BookingsManagement.vue ============
print("\n🔧 Fixing BookingsManagement.vue (script section)...")
content = read_file(f"{VIEWS_DIR}/BookingsManagement.vue")

# 1. Replace the formatDateTime function with formatDate + formatTime
old_func = """function formatDateTime(val: string) {
  if (!val) return ''
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}"""

new_func = """function formatDate(val: string) {
  if (!val) return '-'
  try {
    // Handle YYYY-MM-DD format
    const parts = val.split('-')
    if (parts.length === 3) {
      const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }
    return val
  } catch { return val }
}

function formatTime(val: string) {
  if (!val) return '-'
  try {
    // Handle HH:MM:SS or HH:MM format
    const match = String(val).match(/^(\\d{1,2}):(\\d{2})/)
    if (match) return `${match[1]}:${match[2]}`
    return String(val)
  } catch { return String(val) }
}"""

content = content.replace(old_func, new_func)

# 2. Fix statusBadge - add 'active' mapping
old_badge = """function statusBadge(status: string) {
  const map: Record<string, string> = {
    confirmed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    cancelled: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    done: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
  }
  return map[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}"""

new_badge = """function statusBadge(status: string) {
  const map: Record<string, string> = {
    active: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    confirmed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    cancelled: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    done: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
  }
  return map[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}"""

content = content.replace(old_badge, new_badge)

write_file(f"{VIEWS_DIR}/BookingsManagement.vue", content)
print("  ✅ Script section fixed: formatDate, formatTime added, Active status badge")

# ============ Fix GamesLibrary.vue ============
print("\n🔧 Fixing GamesLibrary.vue...")
content = read_file(f"{VIEWS_DIR}/GamesLibrary.vue")

# 1. Fix deleteItem to use game_title instead of id
old_delete = """async function deleteItem(id: string) {
  if (!confirm('Delete this game?')) return
  try {
    await axios.delete(`/api/dashboard/games/${id}`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}"""

new_delete = """async function deleteItem(game_title: string) {
  if (!confirm('Delete this game?')) return
  try {
    await axios.delete(`/api/dashboard/games/${encodeURIComponent(game_title)}`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}"""

content = content.replace(old_delete, new_delete)

# 2. Fix PUT to use game_title
old_put = """      await axios.put(`/api/dashboard/games/${editing.value.id}`, form.value)"""
new_put = """      await axios.put(`/api/dashboard/games/${encodeURIComponent(editing.value.game_title)}`, form.value)"""
content = content.replace(old_put, new_put)

# 3. Fix template: deleteItem(item.id) → deleteItem(item.game_title)
content = content.replace(
    '@click="deleteItem(item.id)"',
    '@click="deleteItem(item.game_title)"'
)

# 4. Fix: editingItem → editing (that's the actual variable name)
content = content.replace('!!editingItem', '!!editing')

write_file(f"{VIEWS_DIR}/GamesLibrary.vue", content)
print("  ✅ DELETE/PUT use game_title, readonly fixed to use 'editing'")

# ============ Fix FoodStock.vue ============
print("\n🔧 Verifying FoodStock.vue...")
content = read_file(f"{VIEWS_DIR}/FoodStock.vue")
# Check isLowStock
if "item.quantity <= (item.reorder_level || 0)" in content:
    print("  ✅ isLowStock already fixed")
else:
    content = content.replace(
        "item.quantity <= item.reorder_level",
        "item.quantity <= (item.reorder_level || 0)"
    )
    write_file(f"{VIEWS_DIR}/FoodStock.vue", content)
    print("  ✅ isLowStock fixed now")

# ============ Verify MembersManagement.vue ============
print("\n🔧 Verifying MembersManagement.vue...")
content = read_file(f"{VIEWS_DIR}/MembersManagement.vue")
if "animate-spin" in content:
    print("  ✅ Loading spinner present")
if "dark:text-gray-400 uppercase tracking-wider" in content:
    print("  ✅ Dark mode headers present")

# ============ List all views ============
print("\n📁 All view files:")
_, stdout, _ = ssh.exec_command(f"ls -la {VIEWS_DIR}/")
print(stdout.read().decode())

ssh.close()
print("\n✅ Phase 2 fixes applied!")
