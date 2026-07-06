from app.agent import root_agent

for t in root_agent.get_all_tools():
    try:
        decl = t._get_declaration()
        print(f"Tool: {t.name}")
        print(decl.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed to get decl for {t.name}: {e}")
