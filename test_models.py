from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
models = [
    "gemini-2.5-flash",
    "gemini-3.0-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash"
]
client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location="global")
for m in models:
    try:
        resp = client.models.generate_content(model=m, contents='hello')
        print(f"Success for {m}!")
    except Exception as e:
        pass
