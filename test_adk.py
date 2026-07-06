import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app as adk_app


async def main():
    runner = InMemoryRunner(app=adk_app)
    content = types.Content(parts=[types.Part.from_text(text="hi")], role="user")

    try:
        session = await runner.session_service.get_session(
            app_name="app", user_id="u", session_id="s1"
        )
        if not session:
            print("Session doesn't exist, creating.")
            session = await runner.session_service.create_session(
                app_name="app", user_id="u", session_id="s1"
            )

        async for event in runner.run_async(
            user_id="u", session_id="s1", new_message=content
        ):
            print("Event:", event)

    except Exception as e:
        print("Final Error:", e)


asyncio.run(main())
