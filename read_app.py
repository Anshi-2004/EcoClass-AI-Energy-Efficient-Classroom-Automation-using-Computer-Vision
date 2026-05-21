import sys
# Try different encodings to read app.py
for enc in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']:
    try:
        with open('app.py', 'r', encoding=enc) as f:
            content = f.read()
        # Write as UTF-8 to a new file
        with open('app_utf8.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SUCCESS: Read with encoding {enc}, length={len(content)}")
        break
    except Exception as e:
        print(f"FAILED with {enc}: {e}")
