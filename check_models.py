import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- الموديلات المتاحة لحسابك فعلياً ---")
for model in client.models.list():
    if "generateContent" in model.supported_actions:
        print(model.name)