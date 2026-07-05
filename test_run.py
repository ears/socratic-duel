import asyncio
from app.agent import app
from google.adk.runners import InMemoryRunner

async def main():
    runner = InMemoryRunner(app=app)
    async for event in runner.run_async(user_input="Test thesis", user_id="test", session_id="test"):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
