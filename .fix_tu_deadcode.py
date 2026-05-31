import sys

# Read original file
with open('/tmp/members_original.py', 'r') as f:
    lines = f.readlines()

# Find step_tu_kpay function
func_start = None
func_end = None
for i, line in enumerate(lines):
    if 'async def step_tu_kpay(update: Update, context:' in line:
        func_start = i
    elif func_start is not None and line.startswith('@log_duration("members:step_tu_confirm")'):
        func_end = i
        break
    elif func_start is not None and i > func_start + 200:
        # Safety: don't search forever
        func_end = i
        break

print(f'Function: lines {func_start+1}-{func_end}')

# Now extract the function body
func_lines = lines[func_start:func_end]

# Find the dead code zone: after 'return TU_CONFIRM' in the original
# The structure is: cancel/back + methods + BTN_PAY_DONE + review + return TU_CONFIRM + DEAD CODE

# Find the last 'return TU_CONFIRM' which marks the boundary before dead code
last_confirm_idx = None
for i in range(len(func_lines) - 1, -1, -1):
    line = func_lines[i]
    stripped = line.strip()
    if stripped == 'return TU_CONFIRM':
        last_confirm_idx = func_start + i
        break

print(f'Last return TU_CONFIRM at line {last_confirm_idx+1}')

# Find 'return TU_CONFIRM' and the dead code after it
# The amount parsing code starts after the review section
# In original: review → return TU_CONFIRM → dead code (amount parse)

# Now let's find BTN_PAY_DONE to insert BEFORE it
pay_done_idx = None
for i, line in enumerate(func_lines):
    stripped = line.strip()
    if "text == BTN_PAY_DONE" in stripped:
        pay_done_idx = func_start + i
        break

print(f'BTN_PAY_DONE at line {pay_done_idx+1}')

# Now extract the amount parsing code (dead code zone)
dead_code_start = None
dead_code_end = None
for i in range(len(func_lines) - 1, -1, -1):
    line = func_lines[i]
    stripped = line.strip()
    if stripped.startswith('# Try to parse as amount'):
        dead_code_start = func_start + i
        break

# The dead code zone extends to end of function
# Find the next function after step_tu_kpay
next_func_idx = None
for i in range(func_end, min(func_end + 10, len(lines))):
    if lines[i].strip().startswith('@log_duration') or lines[i].strip().startswith('async def'):
        next_func_idx = i
        break

if next_func_idx is None:
    next_func_idx = func_end

dead_code_end = next_func_idx

print(f'Dead code zone: lines {dead_code_start+1}-{dead_code_end}')

# Read the dead code block
print('\n=== DEAD CODE ===')
for line in lines[dead_code_start:dead_code_end]:
    print(line.rstrip())

print('\n=== END DEAD CODE ===')
