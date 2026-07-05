from app.agent import root_agent
from google.adk.tools import FunctionTool, AgentTool
import json

for t in root_agent.tools:
    tool = FunctionTool(t) if not hasattr(t, 'get_function_declaration') else t
    print(tool.get_function_declaration().model_dump_json(indent=2))
