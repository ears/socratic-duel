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

def test_api_chat_start_debate():
    """Test that selecting a lens starts the debate and the protagonist responds."""
    # Step 1: Initialize the session with a valid thesis
    session_id = "test_debate_start_session"
    res1 = client.get(f"/api/chat?message=Artificial%20intelligence%20will%20inevitably%20lead%20to%20the%20obsolescence%20of%20human%20creativity&session_id={session_id}&demo_mode=true")
    assert res1.status_code == 200
    
    # We must consume the stream to let the background tasks finish their turn
    list(res1.iter_lines())
    
    # Step 2: Send the lens choice (e.g., "1" for Empiricist) to start the debate
    res2 = client.get(f"/api/chat?message=1&session_id={session_id}&demo_mode=true")
    assert res2.status_code == 200
    
    events = []
    for line in res2.iter_lines():
        if line and isinstance(line, str) and line.startswith("data: "):
            events.append(line)
            
    has_protagonist_response = False
    for event_str in events:
        event_json_str = event_str[6:]
        if event_json_str.strip() == "": continue
        try:
            event = json.loads(event_json_str)
            if event.get("author") == "protagonist" and event.get("content", "").strip() != "":
                has_protagonist_response = True
                break
        except json.JSONDecodeError:
            pass
            
    assert has_protagonist_response, "The protagonist did not produce an initial argument."

def test_api_chat_rejected_thesis():
    """Test that Triage and analyze properly rejects an invalid/short thesis."""
    response = client.get("/api/chat?message=bad&session_id=test_reject_session&demo_mode=true")
    assert response.status_code == 200
    
    events = []
    for line in response.iter_lines():
        if line and isinstance(line, str) and line.startswith("data: "):
            events.append(line)
            
    has_rejection = False
    for event_str in events:
        event_json_str = event_str[6:]
        if event_json_str.strip() == "": continue
        
        try:
            event = json.loads(event_json_str)
            if event.get("author") == "interactive_planner" and "[STATUS: REJECTED]" in event.get("content", ""):
                has_rejection = True
                break
        except json.JSONDecodeError:
            pass
            
    assert has_rejection, "The analysis phase did not successfully reject a bad thesis."
