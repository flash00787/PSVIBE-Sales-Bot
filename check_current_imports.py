# Check current state of key handler files
files_to_check = [
    'admin.py',
    'main_menu.py',
    'attendance.py',
    'members.py',
    'stock.py',
    'admin_bookings.py',
    'broadcast.py',
]
for fname in files_to_check:
    path = f'/root/Sales-Tele-Bot_refactored/bot/handlers/{fname}'
    with open(path) as f:
        first = f.readline().strip()
        second = f.readline().strip()
    print(f'{fname}: {first} // {second}')
