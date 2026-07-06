import os

os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"

from google import genai

try:
    client = genai.Client()
    response = client.models.generate_content(model="gemini-1.5-flash", contents="hi")
    print("SUCCESS gemini-1.5-flash:", response.text)
except Exception as e:
    print("ERROR gemini-1.5-flash:", e)

try:
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-1.5-flash-001", contents="hi"
    )
    print("SUCCESS gemini-1.5-flash-001:", response.text)
except Exception as e:
    print("ERROR gemini-1.5-flash-001:", e)
