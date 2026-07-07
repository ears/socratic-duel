import asyncio
import json
import os
import re
import warnings

from dotenv import load_dotenv

warnings.filterwarnings("ignore", message=".*\\[EXPERIMENTAL\\].*")
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app as adk_app

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
        session = await runner.session_service.get_session(
            app_name="app", user_id="default_user", session_id=session_id
        )
        if not session:
            await runner.session_service.create_session(
                app_name="app", user_id="default_user", session_id=session_id
            )

        content = types.Content(parts=[types.Part.from_text(text=message)], role="user")
        async for event in runner.run_async(
            user_id="default_user", session_id=session_id, new_message=content
        ):
            # Extract basic text content if available
            text_content = ""
            if hasattr(event, "model_response") and event.model_response:
                try:
                    text_content = event.model_response.text or ""
                except ValueError:
                    pass
            elif (
                hasattr(event, "content")
                and event.content
                and hasattr(event.content, "parts")
            ):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        text_content += part.text

            # Extract tool calls
            tool_calls = []
            if hasattr(event, "tool_calls") and event.tool_calls:
                for tc in event.tool_calls:
                    tool_calls.append({"name": tc.name, "args": tc.args})
            elif (
                hasattr(event, "content")
                and event.content
                and hasattr(event.content, "parts")
            ):
                for part in event.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        tc = part.function_call
                        tool_calls.append({"name": tc.name, "args": tc.args})

            author = getattr(event, "author", "system")
            is_citation_error = False

            if author in ["citation_checker_proto", "citation_checker_anto"]:
                draft_part = ""
                try:
                    # Drop the draft part
                    draft_match = re.search(r"(?i)---(?:DRAFT|ENTWURF).*?---", text_content)
                    if draft_match or "[DRAFT:" in text_content.upper():
                        # Try the new bulletproof separator first
                        if draft_match:
                            split_res = re.split(r"(?i)---(?:DRAFT|ENTWURF).*?---", text_content)
                            status_part = split_res[0]
                            if len(split_res) > 1:
                                draft_part = split_res[1].strip()
                        else:
                            # Fallback to the legacy bracket wrapper
                            split_res = re.split(r"(?i)\[DRAFT:", text_content)
                            status_part = split_res[0]
                            if len(split_res) > 1:
                                draft_part = split_res[1].strip()
                                # ONLY strip the closing bracket if it's literally alone at the end, 
                                # avoiding stripping the Bot Protected tag's bracket.
                                if draft_part.endswith("]") and not draft_part.endswith("[🛡️]"):
                                    draft_part = draft_part[:-1].strip()
                    else:
                        # If no DRAFT tag, assume the first paragraph is status
                        status_part = text_content.split("\n\n")[0]
                        draft_part = text_content[len(status_part):].strip()

                    # Clean up the STATUS tag if it exists
                    status_part = (
                        re.sub(r"(?i)\[STATUS:", "", status_part).strip().rstrip("]")
                    )

                    if "NO_CITATIONS" in status_part.upper():
                        text_content = "No citations to check."
                    elif "VERIFIED" in status_part.upper():
                        matches = re.findall(
                            r"\[([^\[\]]{1,200})\]\(([^\s\)]+)\)\s*\[🛡️\]",
                            draft_part,
                            re.IGNORECASE,
                        )
                        if matches:
                            text_content = (
                                "Citations verified.\n\n🛡️ Bot Protected:\n"
                                + "\n".join([f"- {t}" for t, u in matches])
                            )
                        else:
                            text_content = "Citations verified."
                    elif "ERROR:" in status_part.upper():
                        # Extract all markdown links, ignoring stray characters like commas
                        matches = re.findall(r"\[(.*?)\]\((.*?)\)", status_part)
                        if matches:
                            text_content = "\n".join(
                                [f"- {text}" for text, url in matches]
                            )
                        else:
                            # Fallback if parsing fails
                            text_content = re.sub(
                                r"(?i)ERROR:", "", status_part
                            ).strip()
                        is_citation_error = True
                    else:
                        text_content = status_part
                except Exception:
                    pass

            if author == "judge":
                text_content = text_content.replace("[DECISION: CONTINUE]", "").strip()
                text_content = text_content.replace("[DECISION: END]", "").strip()

            # Clean up any tags that might leak from the citation checkers into the debaters' text
            if author in ["protagonist", "antagonist"]:
                # If the model hallucinated the entire citation checker schema, just extract the draft
                if re.search(r"(?i)---(?:DRAFT|ENTWURF).*?---", text_content):
                    text_content = re.split(r"(?i)---(?:DRAFT|ENTWURF).*?---", text_content)[-1]
                elif "[DRAFT:" in text_content.upper():
                    text_content = re.split(r"(?i)\[DRAFT:", text_content)[-1]

                # Strip out any lingering STATUS tags (whether VERIFIED or ERROR)
                text_content = re.sub(
                    r"(?i)\[STATUS:[^\]]*\]?", "", text_content, flags=re.DOTALL
                )

                text_content = text_content.strip()
                # Remove the trailing bracket from the DRAFT tag if it exists
                if text_content.endswith("]"):
                    text_content = text_content[:-1].strip()

            # Build JSON payload
            payload = {
                "author": author,
                "content": text_content,
                "tool_calls": tool_calls,
                "is_citation_error": is_citation_error,
            }
            if author in ["citation_checker_proto", "citation_checker_anto"]:
                payload["updated_draft"] = draft_part

            yield f"data: {json.dumps(payload)}\n\n"

            # Tiny sleep to allow event loop to yield
            await asyncio.sleep(0.01)

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            error_msg = "The AI model is currently experiencing high demand and we hit a rate limit. Please wait a moment and try again."
        yield f"data: {json.dumps({'author': 'system', 'error': error_msg})}\n\n"


@app.get("/api/chat")
async def chat_endpoint(session_id: str, message: str):
    """
    Initiates a chat stream with the ADK app.
    Usage: EventSource(`/api/chat?session_id=123&message=Hello`)
    """
    return StreamingResponse(
        event_generator(session_id, message), media_type="text/event-stream"
    )


# Mount the static Vite build. This serves both the API and the website on a single port.
frontend_path = os.path.join(os.getcwd(), "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:

    @app.get("/")
    def no_frontend():
        return {
            "message": "Frontend not built yet. Run 'npm run build' in the frontend directory."
        }
