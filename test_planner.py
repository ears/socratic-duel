import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.agent import app

async def main():
    runner = InMemoryRunner(app=app)
    session_id = "test_session_123"
    await runner.session_service.create_session(app_name="app", user_id="user", session_id=session_id)
    
    # Phase 1: User says "AI is good"
    print("--- Phase 1 ---")
    async for event in runner.run_async(user_id="user", session_id=session_id, new_message=types.Content(parts=[types.Part.from_text(text="AI is good")], role="user")):
        if hasattr(event, "model_response"):
            print(event.model_response.text)
        if hasattr(event, "tool_calls"):
            print("Tool calls:", [tc.name for tc in event.tool_calls])
            
    # Phase 2: User selects lens "1"
    print("--- Phase 2 ---")
    async for event in runner.run_async(user_id="user", session_id=session_id, new_message=types.Content(parts=[types.Part.from_text(text="1")], role="user")):
        if hasattr(event, "model_response"):
            print(event.model_response.text)
        if hasattr(event, "tool_calls"):
            print("Tool calls:", [tc.name for tc in event.tool_calls])
            
asyncio.run(main())
