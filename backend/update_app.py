import re

with open("backend/app.py", "r") as f:
    content = f.read()

# Pass model_id to chains
content = re.sub(
    r'(chunk_gen = run_[a-z_]+_chain\([^\)]*?)(, stream=True\))', 
    r'\1, model_id=req.model_id\2', 
    content
)

# Fix run_document_qa_chain which has a different signature in app.py: (req.message, req.message, stream=True)
content = re.sub(
    r'run_document_qa_chain\(req.message, req.message, model_id=req.model_id, stream=True\)',
    r'run_document_qa_chain(req.message, req.message, stream=True, model_id=req.model_id)',
    content
)

with open("backend/app.py", "w") as f:
    f.write(content)
