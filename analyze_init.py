import re
import sys

# Read all content from the output we got
content = sys.stdin.read()

# Find __all__ list 
m = re.search(r'__all__\s*=\s*\[(.*?)\]', content, re.DOTALL)
all_names = set()
if m:
    for name in re.findall(r"'([^']+)'", m.group(1)):
        all_names.add(name)

# Find all top-level definitions
defined_names = set()
for m in re.finditer(r'^(?:async\s+)?def\s+(\w+)', content, re.MULTILINE):
    defined_names.add(m.group(1))
for m in re.finditer(r'^class\s+(\w+)', content, re.MULTILINE):
    defined_names.add(m.group(1))
for m in re.finditer(r'^(\w+)\s*=\s*', content, re.MULTILINE):
    name = m.group(1)
    if name not in ('import', 'from', 'if', 'elif', 'else', 'for', 'while', 'try', 'with', 'return', 'pass', 'raise', 'yield', 'break', 'continue', 'global', 'nonlocal', 'assert', 'del', 'True', 'False', 'None'):
        defined_names.add(name)

# In __all__ but not defined
missing = all_names - defined_names
print('=== In __all__ but NOT defined ===')
for name in sorted(missing):
    print(f'  MISSING: {name}')

# Defined but not in __all__
private_n = {n for n in defined_names - all_names if n.startswith('_')}
public_n = {n for n in defined_names - all_names - private_n if not n.startswith('__')}

print(f'\n=== Public names defined but NOT in __all__ ({len(public_n)}) ===')
for name in sorted(public_n):
    print(f'  {name}')

# Duplicate definitions check
from collections import Counter
def_counter = Counter()
for m in re.finditer(r'^(?:async\s+)?def\s+(\w+)', content, re.MULTILINE):
    def_counter[m.group(1)] += 1
for m in re.finditer(r'^class\s+(\w+)', content, re.MULTILINE):
    def_counter[m.group(1)] += 1

dupes = {k: v for k, v in def_counter.items() if v > 1}
if dupes:
    print('\n=== DUPLICATE definitions ===')
    for k, v in dupes.items():
        print(f'  {k}: defined {v} times')

print(f'\nTotal names in __all__: {len(all_names)}')
print(f'Total defined names: {len(defined_names)}')
