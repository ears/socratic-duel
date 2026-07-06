import asyncio

from google.adk.runners import InMemoryRunner

from app.agent import app


async def main():
    runner = InMemoryRunner(app=app)
    # The root agent is wrapped by the runner. Let's get its tools.
    tools = runner.agent._get_all_tools()
    for t in tools:
        print("Tool Name:", t.name)
        try:
            print(t._get_declaration().model_dump_json(indent=2))
        except Exception as e:
            print("Could not dump schema:", e)


asyncio.run(main())
