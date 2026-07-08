import asyncio
from app.agent import app

async def main():
    session_id = "test1234"
    async for event in app.stream("Test thesis", session_id=session_id):
        print(f"Event: {event}")

asyncio.run(main())
