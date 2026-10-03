from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
for m in client.models.list().data:
    print(m.id)