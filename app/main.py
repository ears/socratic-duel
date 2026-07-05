import os
import json
import asyncio
import re
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.agent import app as adk_app
from google.adk.runners import InMemoryRunner
from google.genai import types

app = FastAPI(title="Socratic Duel API")
runner = InMemoryRunner(app=adk_app)

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def event_generator(session_id: str, message: str):
    """
    Streams ADK events to the client using Server-Sent Events (SSE).
    This enables the 'Live Dialectical Debate UI' (Phase 3) where the user can 'read along'.
    """
    try:
        # Ensure the session exists in memory before attempting to run or resume it
        session = await runner.session_service.get_session(app_name="app", user_id="default_user", session_id=session_id)
        if not session:
            await runner.session_service.create_session(app_name="app", user_id="default_user", session_id=session_id)

        content = types.Content(parts=[types.Part.from_text(text=message)], role="user")
        async for event in runner.run_async(user_id="default_user", session_id=session_id, new_message=content):
            # Extract basic text content if available
            text_content = ""
            if hasattr(event, "model_response") and event.model_response:
                try:
                    text_content = event.model_response.text or ""
                except ValueError:
                    pass
            elif hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        text_content += part.text
            
            # Extract tool calls
            tool_calls = []
            if hasattr(event, "tool_calls") and event.tool_calls:
                for tc in event.tool_calls:
                    tool_calls.append({"name": tc.name, "args": tc.args})
            elif hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        tc = part.function_call
                        tool_calls.append({"name": tc.name, "args": tc.args})

            author = getattr(event, "author", "system")
            is_citation_error = False
            
            if author in ["citation_checker_proto", "citation_checker_anto"] and "[STATUS:" in text_content:
                try:
                    status_part = text_content.split("[STATUS:")[1].split("[DRAFT:")[0].strip().rstrip("]")
                    if "NO_CITATIONS" in status_part:
                        text_content = "No citations to check."
                    elif "VERIFIED" in status_part:
                        text_content = "Citations verified."
                    elif "ERROR:" in status_part:
                        # Extract everything after ERROR:
                        error_text = status_part.split("ERROR:")[1].strip()
                        # Format [Text](URL) as Text (URL)
                        text_content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', error_text)
                        is_citation_error = True
                    else:
                        text_content = status_part
                except IndexError:
                    pass

            if author == "judge":
                text_content = text_content.replace("[DECISION: CONTINUE]", "").strip()
                text_content = text_content.replace("[DECISION: END]", "").strip()

            # Clean up any tags that might leak from the citation checkers into the debaters' text
            if author in ["protagonist", "antagonist"]:
                text_content = text_content.replace("[STATUS: VERIFIED]", "").strip()
                text_content = text_content.replace("[DRAFT:", "").strip()
                if text_content.endswith("]"):
                    text_content = text_content[:-1].strip()

            # Build JSON payload
            payload = {
                "author": author,
                "content": text_content,
                "tool_calls": tool_calls,
                "is_citation_error": is_citation_error
            }
            
            yield f"data: {json.dumps(payload)}\n\n"
            
            # Tiny sleep to allow event loop to yield
            await asyncio.sleep(0.01)
            
    except Exception as e:
        yield f"data: {json.dumps({'author': 'system', 'error': str(e)})}\n\n"

@app.get("/api/chat")
async def chat_endpoint(session_id: str, message: str):
    """
    Initiates a chat stream with the ADK app.
    Usage: EventSource(`/api/chat?session_id=123&message=Hello`)
    """
    return StreamingResponse(event_generator(session_id, message), media_type="text/event-stream")

# Mount the static Vite build. This serves both the API and the website on a single port.
frontend_path = os.path.join(os.getcwd(), "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    @app.get("/")
    def no_frontend():
        return {"message": "Frontend not built yet. Run 'npm run build' in the frontend directory."}
