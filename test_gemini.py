import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print("Key loaded:", "YES" if api_key else "NO - CHECK .env FILE")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Say 'Gemini connection successful' and nothing else."
)
print(response.text)