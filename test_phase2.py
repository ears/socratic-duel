import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner

from app.agent import app as adk_app

load_dotenv()

async def main():
    runner = InMemoryRunner(app=adk_app)

    print("=== PHASE 1 ===")
    await runner.session_service.create_session(app_name="app", user_id="u", session_id="test_session")
    from app.main import event_generator

    # Phase 1
    content1 = "I believe AI will replace all software engineers within 5 years."
    async for chunk in event_generator(session_id="test_session", message=content1):
        print("P1 CHUNK:", chunk)

    print("\n=== PHASE 2 ===")
    content2 = "1"
    async for chunk in event_generator(session_id="test_session", message=content2):
        print("P2 CHUNK:", chunk)

asyncio.run(main())
