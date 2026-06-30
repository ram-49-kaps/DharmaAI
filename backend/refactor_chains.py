import glob
import re

files = glob.glob("chains/*.py")
skip_files = ["__init__.py", "leveling.py", "router.py", "thinking.py"]

for f in files:
    filename = f.split('/')[-1]
    if filename in skip_files:
        continue
    with open(f, 'r') as file:
        content = file.read()
    
    # Replace def run_..._chain(message: str, ...) -> str:
    # with def run_..._chain(message: str, ..., stream: bool = False):
    content = re.sub(r'(def run_[a-z_]+_chain\([^)]*\))(?: -> str)?:', r'\1, stream: bool = False):', content)
    
    # In some cases, we need to handle cases where there are no arguments or different arguments,
    # wait, the regex above will append `, stream: bool = False` inside or outside the parens?
    # Actually, `\1` includes the closing parenthesis. So it becomes `def ...), stream: bool = False):` which is a SYNTAX ERROR.
    
    # Correct regex:
    # Match `def func(args)` and replace with `def func(args, stream=False)`
    content = re.sub(r'(def run_[a-z_]+_chain\([^)]*)(\))(?: -> str)?:', r'\1, stream: bool = False\2:', content)
    
    # Replace invoke_with_fallback(..., inputs) with invoke_with_fallback(..., inputs, stream=stream)
    content = re.sub(r'(invoke_with_fallback\([\s\S]*?inputs)(\s*\))', r'\1, stream=stream\2', content)
    
    with open(f, 'w') as file:
        file.write(content)

print("Updated chains")
