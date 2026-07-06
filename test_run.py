import asyncio

from google.adk.runners import InMemoryRunner

from app.agent import app


async def main():
    runner = InMemoryRunner(app=app)
    async for event in runner.run_async(
        user_input="Test thesis", user_id="test", session_id="test"
    ):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
