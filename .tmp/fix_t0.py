with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    lines = f.readlines()

target_phrase = 'User picked a console to end'
found_idx = -1
# Find where the step_end_session docstring starts
for i, line in enumerate(lines):
    if target_phrase in line and 'find its booking' in line:
        found_idx = i
        print(f'Found docstring at line {i+1}')
        break

if found_idx >= 0:
    # The next line (after docstring closing) should have "text ="
    insert_before = -1
    for j in range(found_idx, min(found_idx + 5, len(lines))):
        if lines[j].strip().startswith('text') and '= update.message.text.strip()' in lines[j]:
            insert_before = j
            break
    
    if insert_before > 0:
        lines.insert(insert_before, '    _t0 = time.monotonic()\n')
        print(f'Inserted _t0 before line {insert_before + 1}')
    else:
        print(f'Could not find text = line after docstring')
        print(f'Lines around found_idx:')
        for j in range(found_idx, min(found_idx + 6, len(lines))):
            print(f'  Line {j+1}: {repr(lines[j][:80])}')
else:
    print(f'Docstring not found!')
    for i, line in enumerate(lines):
        if 'def step_end_session' in line:
            print(f'def found at line {i+1}')
            for j in range(i, min(i+6, len(lines))):
                print(f'  Line {j+1}: {repr(lines[j][:80])}')
            break

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.writelines(lines)
print('DONE')
