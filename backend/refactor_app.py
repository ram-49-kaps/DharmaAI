import re

with open("app.py", "r") as f:
    content = f.read()

# Add StreamingResponse to imports
if "StreamingResponse" not in content:
    content = content.replace("from fastapi import FastAPI, Request, HTTPException, Depends", "from fastapi import FastAPI, Request, HTTPException, Depends\nfrom fastapi.responses import StreamingResponse")
    content = content.replace("from fastapi import FastAPI, Depends, HTTPException, Request, Response", "from fastapi import FastAPI, Depends, HTTPException, Request, Response\nfrom fastapi.responses import StreamingResponse")
    content = content.replace("from fastapi.responses import JSONResponse", "from fastapi.responses import JSONResponse, StreamingResponse")

if "import uuid" not in content:
    content = content.replace("import json", "import json\nimport uuid")

if "import time" not in content:
    content = content.replace("import uuid", "import uuid\nimport time")

# We'll just replace the entire `chat` function
new_chat_func = '''@app.post("/api/chat")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    """RAG-first chat endpoint. All queries retrieve before generating (SSE stream)."""
    req = await _chat_request_from_request(request)
    
    async def event_generator():
        try:
            history_dicts = [m.model_dump() for m in req.history]
            level = req.level or _get_saved_profile(user.get("uid", "anonymous"), user).level
            
            response_id = str(uuid.uuid4())
            timestamp = int(time.time() * 1000)

            # 1. Determine Intent
            if is_follow_up(req.message) and history_dicts:
                intent = "follow_up"
            else:
                intent = detect_intent(req.message)

            # 2. Status event: Intent detected
            yield f"data: {json.dumps({'type': 'status', 'data': f'Detected intent: {intent}'})}\\n\\n"

            # 3. Retrieve sources immediately (so we can stream metadata)
            sources = []
            citations = []
            if intent != "conversational":
                yield f"data: {json.dumps({'type': 'status', 'data': 'Searching knowledge base...'})}\\n\\n"
                engine = get_rag_engine()
                _, raw_results = engine.retrieve(req.message, k_final=8)
                seen = set()
                for r in raw_results:
                    meta = r.get("metadata", {})
                    title = meta.get("title", "")
                    if title in seen:
                        continue
                    seen.add(title)
                    sources.append(Source(
                        title=title,
                        type=meta.get("source_type", meta.get("category", "statute")).lower(),
                        citation=meta.get("citation", ""),
                        page=meta.get("page", ""),
                        excerpt=r.get("content", "")[:200],
                    ))
                citations = _sources_to_citations(sources)

            # 4. Yield Metadata
            yield f"data: {json.dumps({'type': 'metadata', 'data': {'intent': intent, 'sources': [s.model_dump() for s in sources], 'citations': citations, 'response_id': response_id, 'timestamp': timestamp}})}\\n\\n"

            # 5. Determine which chain to stream
            yield f"data: {json.dumps({'type': 'status', 'data': 'Generating response...'})}\\n\\n"
            
            if intent == "follow_up":
                chunk_gen = run_follow_up_chain(req.message, history_dicts, level=level, stream=True)
            elif intent == "definition":
                chunk_gen = run_definition_chain(req.message, level=level, stream=True)
            elif intent == "case_lookup":
                chunk_gen = run_caselaw_chain(req.message, level=level, stream=True)
            elif intent == "statute_lookup":
                chunk_gen = run_statute_chain(req.message, level=level, stream=True)
            elif intent == "irac_analysis":
                chunk_gen = run_irac_chain(req.message, level=level, stream=True)
            elif intent == "filac_analysis":
                chunk_gen = run_filac_chain(req.message, level=level, stream=True)
            elif intent == "idar_analysis":
                chunk_gen = run_idar_chain(req.message, level=level, stream=True)
            elif intent == "comparative":
                chunk_gen = run_general_chain(req.message, history_dicts, level=level, stream=True)
            elif intent == "conversational":
                chunk_gen = run_conversational_chain(req.message, stream=True)
            else:
                chunk_gen = run_general_chain(req.message, history_dicts, level=level, stream=True)

            # 6. Stream chunks
            full_answer = ""
            for chunk in chunk_gen:
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk})}\\n\\n"
            
            # 7. Generate suggestions
            suggested_questions = []
            if intent != "conversational" and full_answer:
                yield f"data: {json.dumps({'type': 'status', 'data': 'Generating suggestions...'})}\\n\\n"
                from chains.follow_up import generate_suggested_questions
                suggested = generate_suggested_questions(req.message, full_answer)
                if suggested:
                    for line in suggested.split("\\n"):
                        line_clean = line.strip()
                        if line_clean.startswith(("- ", "* ")):
                            q = line_clean[2:].strip()
                            if q:
                                suggested_questions.append(q)
                yield f"data: {json.dumps({'type': 'suggestions', 'data': suggested_questions})}\\n\\n"
            
            # 8. Done event
            yield f"data: {json.dumps({'type': 'done'})}\\n\\n"

        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
'''

# Find the start and end of the chat function
start_idx = content.find('@app.post("/api/chat"')
end_idx = content.find('# ── Thinking', start_idx)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_chat_func + "\n\n" + content[end_idx:]
    with open("app.py", "w") as f:
        f.write(content)
    print("Successfully replaced chat function")
else:
    print("Could not find chat function boundaries")
