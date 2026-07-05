import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.agent import app as adk_app

app = FastAPI(title="Epistemic Synthesizer API")

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
        async for event in adk_app.run(session_id=session_id, message=message):
            # Extract basic text content if available
            text_content = ""
            if hasattr(event, "model_response") and event.model_response and event.model_response.contents:
                for part in event.model_response.contents[0].parts:
                    if part.text:
                        text_content += part.text

            # Extract tool calls (like set_chosen_lens, google_search)
            tool_calls = []
            if hasattr(event, "tool_calls") and event.tool_calls:
                for tc in event.tool_calls:
                    tool_calls.append({"name": tc.name, "args": tc.args})

            # Build JSON payload
            payload = {
                "author": event.author,
                "content": text_content,
                "tool_calls": tool_calls
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
