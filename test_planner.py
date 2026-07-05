from app.agent import root_agent
from google.adk.tools.utils import extract_tool_declarations
from google.adk.utils.variant_utils import GoogleLLMVariant

for t in root_agent.get_all_tools():
    try:
        decl = t._get_declaration()
        print(f"Tool: {t.name}")
        print(decl.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed to get decl for {t.name}: {e}")
