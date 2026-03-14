"""
Detailed Log Error Finder
"""

log_file = './logs/api/api.log'

print("Searching for errors in API log...")
print("="*80)

with open(log_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
error_lines = []
for i, line in enumerate(lines):
    if '500' in line or 'ERROR' in line or 'Exception' in line or 'Traceback' in line:
        error_lines.append((i+1, line.strip()))

if error_lines:
    print(f"Found {len(error_lines)} potential error lines:")
    print()
    for line_num, line in error_lines[:20]:  # Show first 20
        print(f"Line {line_num}: {line[:200]}")
else:
    print("No errors found!")

print()
print("="*80)

# Check for 404s
print("\nSearching for 404 errors...")
not_found = []
for i, line in enumerate(lines):
    if '404' in line:
        not_found.append((i+1, line.strip()))

if not_found:
    print(f"Found {len(not_found)} 404 errors:")
    for line_num, line in not_found[:10]:
        print(f"Line {line_num}: {line[:200]}")
