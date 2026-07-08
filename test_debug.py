from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/api/chat?message=Artificial%20intelligence%20will%20inevitably%20lead%20to%20the%20obsolescence%20of%20human%20creativity&session_id=test_demo_session&demo_mode=true")

for line in response.iter_lines():
    if line and isinstance(line, str) and line.startswith("data: "):
        print(line)
