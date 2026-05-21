import os
import shutil

# Read the fixed file
with open('app_fixed.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Delete original app.py and write new one
try:
    os.remove('app.py')
except:
    pass

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: app.py has been replaced with app_fixed.py content")
print(f"File size: {os.path.getsize('app.py')} bytes")

# Clean up
os.remove('app_fixed.py')
os.remove('fix_encoding.py')
print("Cleanup done")
