import glob
import re

files = glob.glob("chains/*.py")
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    # Fix the syntax error: `None), stream: bool = False):` -> `None, stream: bool = False):`
    content = content.replace("), stream: bool = False):", ", stream: bool = False):")
    
    with open(f, 'w') as file:
        file.write(content)
print("Fixed syntax errors")
