from langchain_groq import ChatGroq
from tavily import TavilyClient
from config import GROQ_API_KEY, TAVILY_API_KEY, MODEL_NAME

# Test 1: talk to the LLM
llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
reply = llm.invoke("Say hello in one short sentence.")
print("GROQ SAYS:", reply.content)

# Test 2: search the web
tavily = TavilyClient(api_key=TAVILY_API_KEY)
results = tavily.search("what is LangGraph", max_results=3)
print("\nTAVILY FOUND:")
for r in results["results"]:
    print("-", r["title"])