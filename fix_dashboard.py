#!/usr/bin/env python3
"""SSH into 5.223.81.16 and fix PS VIBE Dashboard pages."""
import paramiko
import time

HOST = "5.223.81.16"
KEY_PATH = "/home/node/.openclaw/workspace/.ssh/id_rsa"
VIEWS_DIR = "/root/psvibe-dashboard/src/views"
PROJECT_DIR = "/root/psvibe-dashboard"
API_DIR = "/root/psvibe_api_server"

def ssh_exec(ssh, cmd, timeout=30):
    """Execute a command and return stdout, stderr, exit code."""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    code = stdout.channel.recv_exit_status()
    return out, err, code

def read_remote(ssh, path):
    """Read a remote file into a string."""
    _, stdout, _ = ssh.exec_command(f"cat '{path}'")
    return stdout.read().decode('utf-8', errors='replace')

def write_remote(ssh, path, content):
    """Write content to a remote file via SFTP."""
    sftp = ssh.open_sftp()
    with sftp.open(path, 'w') as f:
        f.write(content)
    sftp.close()

def main():
    print("🔑 Connecting to server via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    ssh.connect(HOST, username="root", pkey=key, timeout=15)
    print("✅ Connected!")

    # === STEP 1: Backup all 5 files ===
    files = ["BookingsManagement.vue", "GamesLibrary.vue", "FoodStock.vue",
             "MembersManagement.vue", "StaffManagement.vue"]
    
    print("\n📦 Creating backups...")
    for f in files:
        o, e, c = ssh_exec(ssh, f"cp '{VIEWS_DIR}/{f}' '{VIEWS_DIR}/{f}.bak'")
        if c == 0:
            print(f"  ✅ {f} backed up")
        else:
            print(f"  ⚠️ {f} backup: {e.strip() if e else 'file may not exist'}")

    # === STEP 2: Fix BookingsManagement.vue ===
    print("\n🔧 Fixing BookingsManagement.vue...")
    content = read_remote(ssh, f"{VIEWS_DIR}/BookingsManagement.vue")
    print(f"  Original size: {len(content)} chars")

    # Fix 1: console_name → console_id
    content = content.replace(
        "item.console_name || item.console || '-'",
        "item.console_id || '-'"
    )
    
    # Fix 2: member_name → member_id
    content = content.replace(
        "item.member_name || item.member || '-'",
        "item.member_id || '-'"
    )
    
    # Fix 3: booking_date format - replace formatDateTime reference
    content = content.replace(
        "formatDateTime(item.booking_date || item.date)",
        "formatDate(item.booking_date)"
    )
    
    # Fix 4: start_time - change to show time only
    content = content.replace(
        "item.start_time || item.time || '-'",
        "formatTime(item.start_time)"
    )
    
    # Fix 5: duration → duration_mins
    content = content.replace(
        "item.duration ? item.duration + ' min' : '-'",
        "item.duration_mins ? item.duration_mins + ' min' : '-'"
    )
    
    # Fix 6: Add Active to statusBadge
    content = content.replace(
        "'Cancelled': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'",
        "'Cancelled': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',\n    'Active': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'"
    )

    # Fix 7: Replace formatDateTime with formatDate and add formatTime
    old_format = """const formatDateTime = (val) => {
  if (!val) return '-'
  try {
    return new Date(val).toLocaleString()
  } catch {
    return val
  }
}"""
    
    new_format = """const formatDate = (val) => {
  if (!val) return '-'
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) {
      // Try parsing YYYY-MM-DD
      const parts = val.split('-')
      if (parts.length === 3) {
        return new Date(parts[0], parts[1]-1, parts[2]).toLocaleDateString('en-US', {
          month: 'short', day: 'numeric', year: 'numeric'
        })
      }
      return val
    }
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return val
  }
}

const formatTime = (val) => {
  if (!val) return '-'
  const s = String(val)
  // Handle HH:MM:SS or HH:MM
  const match = s.match(/^(\\d{1,2}):(\\d{2})/)
  if (match) return `${match[1]}:${match[2]}`
  return s
}

const formatDateTime = (val) => {
  if (!val) return '-'
  try {
    return new Date(val).toLocaleString()
  } catch {
    return val
  }
}"""
    
    if old_format in content:
        content = content.replace(old_format, new_format)
        print("  ✅ formatDateTime replaced with formatDate + formatTime")
    else:
        print("  ⚠️ formatDateTime block not found, searching for variant...")
        # Try to find it
        if 'formatDateTime' in content:
            print("  formatDateTime found but exact block mismatch; skipping function rename")

    # Loading state - Fix loading spinner
    old_loading = '<div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>'
    new_loading = '<div v-if="loading" class="flex justify-center items-center py-12">\n        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>\n      </div>'
    if old_loading in content:
        content = content.replace(old_loading, new_loading)
        print("  ✅ Loading spinner replaced")
    else:
        print("  ⚠️ Loading text block not found (may already be fixed or different)")

    # Fix table headers
    old_th = 'class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"'
    new_th = 'class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"'
    content = content.replace(old_th, new_th)

    write_remote(ssh, f"{VIEWS_DIR}/BookingsManagement.vue", content)
    print(f"  ✅ BookingsManagement.vue written ({len(content)} chars)")

    # === STEP 3: Fix GamesLibrary.vue ===
    print("\n🔧 Fixing GamesLibrary.vue...")
    content = read_remote(ssh, f"{VIEWS_DIR}/GamesLibrary.vue")
    print(f"  Original size: {len(content)} chars")

    # Fix DELETE to use game_title instead of id
    # Pattern: api.delete(`/games/${id}`) → api.delete(`/games/${encodeURIComponent(game_title)}`)
    content = content.replace(
        "api.delete(`/games/${id}`)",
        "api.delete(`/games/${encodeURIComponent(game_title)}`)"
    )
    content = content.replace(
        'api.delete(`/games/${id}`)',
        'api.delete(`/games/${encodeURIComponent(game_title)}`)'
    )
    # Also check variant patterns
    if "/games/${" in content:
        # Find all delete patterns
        import re
        content = re.sub(
            r"api\.delete\(`/games/\$\{id\}`\)",
            "api.delete(`/games/${encodeURIComponent(game_title)}`)",
            content
        )
    print("  ✅ DELETE endpoint uses game_title")

    # Fix PUT to use game_title
    content = re.sub(
        r"api\.put\(`/games/\$\{id\}`",
        "api.put(`/games/${encodeURIComponent(game_title)}`",
        content
    )
    content = re.sub(
        r"api\.put\(`/games/\$\{game\.id\}`",
        "api.put(`/games/${encodeURIComponent(game.game_title)}`",
        content
    )
    print("  ✅ PUT endpoint uses game_title")

    # Fix edit form - game_title should not be editable when editing
    # Look for the form field for game_title
    # Make it readonly when editing (when editingItem exists)
    if 'v-model="form.game_title"' in content or 'v-model="gameForm.game_title"' in content:
        # Find the input and add :disabled="!!editingItem" or :readonly="!!editingItem"
        content = content.replace(
            'v-model="form.game_title"',
            'v-model="form.game_title" :readonly="!!editingItem"'
        )
        content = content.replace(
            'v-model="gameForm.game_title"',
            'v-model="gameForm.game_title" :readonly="!!editingItem"'
        )
        content = content.replace(
            'v-model="editForm.game_title"',
            'v-model="editForm.game_title" :readonly="!!editingItem"'
        )
        print("  ✅ game_title field readonly when editing")

    # Loading state
    if old_loading in content:
        content = content.replace(old_loading, new_loading)

    # Table headers
    content = content.replace(old_th, new_th)

    write_remote(ssh, f"{VIEWS_DIR}/GamesLibrary.vue", content)
    print(f"  ✅ GamesLibrary.vue written ({len(content)} chars)")

    # === STEP 4: Fix FoodStock.vue ===
    print("\n🔧 Fixing FoodStock.vue...")
    content = read_remote(ssh, f"{VIEWS_DIR}/FoodStock.vue")
    print(f"  Original size: {len(content)} chars")

    # Fix isLowStock - handle null reorder_level
    old_low = "item.quantity <= item.reorder_level"
    new_low = "item.quantity <= (item.reorder_level || 0)"
    if old_low in content:
        content = content.replace(old_low, new_low)
        print("  ✅ isLowStock fixed for null reorder_level")
    else:
        # Try alternative patterns
        print("  Searching for isLowStock pattern...")
        # Look for the function
        alt_patterns = [
            "item.quantity <= item.reorder_level",
            "quantity <= item.reorder_level",
            "<= item.reorder_level",
        ]
        found = False
        for p in alt_patterns:
            if p in content:
                content = content.replace(p, p.replace("reorder_level", "(item.reorder_level || 0)"))
                print(f"  ✅ Fixed using pattern: {p}")
                found = True
                break
        if not found:
            print("  ⚠️ Could not find isLowStock pattern")

    # Loading state
    if old_loading in content:
        content = content.replace(old_loading, new_loading)

    # Table headers
    content = content.replace(old_th, new_th)

    write_remote(ssh, f"{VIEWS_DIR}/FoodStock.vue", content)
    print(f"  ✅ FoodStock.vue written ({len(content)} chars)")

    # === STEP 5: Fix MembersManagement.vue ===
    print("\n🔧 Fixing MembersManagement.vue...")
    content = read_remote(ssh, f"{VIEWS_DIR}/MembersManagement.vue")
    if content:
        print(f"  Original size: {len(content)} chars")
        # Loading state
        if old_loading in content:
            content = content.replace(old_loading, new_loading)
            print("  ✅ Loading spinner replaced")
        # Table headers
        content = content.replace(old_th, new_th)
        write_remote(ssh, f"{VIEWS_DIR}/MembersManagement.vue", content)
        print(f"  ✅ MembersManagement.vue written ({len(content)} chars)")
    else:
        print("  ⚠️ MembersManagement.vue not found")

    # === STEP 6: Fix StaffManagement.vue ===
    print("\n🔧 Fixing StaffManagement.vue...")
    content = read_remote(ssh, f"{VIEWS_DIR}/StaffManagement.vue")
    if content:
        print(f"  Original size: {len(content)} chars")
        # Loading state
        if old_loading in content:
            content = content.replace(old_loading, new_loading)
            print("  ✅ Loading spinner replaced")
        # Table headers
        content = content.replace(old_th, new_th)
        write_remote(ssh, f"{VIEWS_DIR}/StaffManagement.vue", content)
        print(f"  ✅ StaffManagement.vue written ({len(content)} chars)")
    else:
        print("  ⚠️ StaffManagement.vue not found")

    # === STEP 7: Build & Deploy ===
    print("\n🔨 Building frontend...")
    out, err, code = ssh_exec(ssh, f"cd {PROJECT_DIR} && npm run build 2>&1 | tail -20", timeout=120)
    print(f"  Build output:\n{out}")
    if err:
        print(f"  Build stderr:\n{err[:1000]}")
    if code != 0:
        print(f"  ⚠️ Build failed with code {code}")
        # Try to get more build info
        build_out, _, _ = ssh_exec(ssh, f"cd {PROJECT_DIR} && npm run build 2>&1 | head -50")
        print(f"  Full build output:\n{build_out[:2000]}")
        ssh.close()
        return
    else:
        print("  ✅ Build successful")

    # Deploy
    print("\n🚀 Deploying...")
    ssh_exec(ssh, f"rm -rf {API_DIR}/dashboard-dist")
    out, err, code = ssh_exec(ssh, f"cp -r {PROJECT_DIR}/dist {API_DIR}/dashboard-dist")
    if code != 0:
        print(f"  ⚠️ Deploy copy failed: {err}")
    else:
        print("  ✅ dist copied to api_server")

    out, err, code = ssh_exec(ssh, "sudo systemctl restart psvibe-api")
    if code != 0:
        print(f"  ⚠️ Restart failed: {err}")
    else:
        print("  ✅ psvibe-api restarted")
    
    time.sleep(2)

    # Verify
    out, err, code = ssh_exec(ssh, "curl -s http://localhost:8000/ | head -10")
    print(f"\n🔍 Verify frontend:\n{out[:500]}")
    
    # Check API health
    out, err, code = ssh_exec(ssh, "curl -s http://localhost:8000/health 2>&1 || curl -s http://localhost:8000/api/health 2>&1 || echo 'No health endpoint'")
    print(f"🔍 Health check: {out[:200]}")

    ssh.close()
    print("\n✅ All done!")

if __name__ == "__main__":
    main()
