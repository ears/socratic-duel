from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
models = [
    "gemini-2.5-pro",
    "gemini-3-pro-preview",
    "gemini-3.1-pro-preview",
    "gemini-3.1-pro",
    "gemini-3.1-flash",
    "gemini-3.1-flash-lite"
]
client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location="global")
for m in models:
    try:
        resp = client.models.generate_content(model=m, contents='hello')
        print(f"Success for {m}!")
    except Exception as e:
        pass
