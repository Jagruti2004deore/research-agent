import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MODEL_NAME = "openai/gpt-oss-120b"

if not GROQ_API_KEY or not TAVILY_API_KEY:
    raise ValueError("Missing API keys. Check your .env file.")