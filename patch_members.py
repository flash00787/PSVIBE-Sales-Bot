import re

path = 'src/views/MembersManagement.vue'
with open(path, 'r') as f:
    content = f.read()

# Add Delete button after Edit button in Actions column
old = '<td class="px-4 py-3 text-right text-sm" @click.stop>\n                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3 transition-colors">Edit</button>\n              </td>'
new = '<td class="px-4 py-3 text-right text-sm" @click.stop>\n                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3 transition-colors">Edit</button>\n                <button @click="deleteItem(item.member_id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>\n              </td>'

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('MembersManagement.vue: Delete button added')
else:
    print('Pattern not found, trying alternate...')
    # Try to find the edit button line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'openEdit(item)' in line and 'Edit' in line:
            print(f'Found Edit at line {i+1}: {line.strip()}')
            # Show surrounding lines
            for j in range(max(0,i-2), min(len(lines), i+3)):
                print(f'  {j+1}: {lines[j].rstrip()}')
            break
