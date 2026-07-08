import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_chat_demo_mode():
    """Test that Triage and analyze (demo mode) returns correctly formatted SSE events."""
    response = client.get("/api/chat?message=Artificial%20intelligence%20will%20inevitably%20lead%20to%20the%20obsolescence%20of%20human%20creativity&session_id=test_demo_session&demo_mode=true")
    assert response.status_code == 200
    
    events = []
    # TestClient doesn't stream natively in the same way, but it collects all content.
    for line in response.iter_lines():
        if line and isinstance(line, str) and line.startswith("data: "):
            events.append(line)
                
    # Check that we received some events
    assert len(events) > 0, "No events returned from the streaming endpoint"
    
    # Check that the analysis phase output is returned in the stream
    has_analysis = False
    for event_str in events:
        event_json_str = event_str[6:] # Strip "data: "
        if event_json_str.strip() == "": continue
        
        try:
            event = json.loads(event_json_str)
            if event.get("author") == "interactive_planner" and event.get("content", "").strip() != "":
                if "[STATUS: REJECTED]" not in event.get("content", ""):
                    has_analysis = True
                    break
        except json.JSONDecodeError:
            pass
            
    assert has_analysis, "The analysis phase did not successfully complete and return a valid triage analysis."
