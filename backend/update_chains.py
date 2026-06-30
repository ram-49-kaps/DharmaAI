import glob
import re

for filepath in glob.glob("backend/chains/*.py"):
    with open(filepath, "r") as f:
        content = f.read()
    
    if "invoke_with_fallback" in content and "def run_" in content:
        # replace def run_*(..., stream: bool = False): -> , model_id: str = None):
        content = re.sub(r'(def run_[a-z_]+_chain\(.*?stream: bool = False)\):', r'\1, model_id: str = None):', content)
        
        # for chains that don't have stream: bool = False at the end of args
        content = re.sub(r'(def run_[a-z_]+_chain\(.*?history: list = None)\):', r'\1, model_id: str = None):', content)

        # replace stream=stream) with stream=stream, model_id=model_id)
        content = re.sub(r'(invoke_with_fallback\([\s\S]*?stream=stream)', r'\1, model_id=model_id', content)

        with open(filepath, "w") as f:
            f.write(content)
        print(f"Updated {filepath}")
