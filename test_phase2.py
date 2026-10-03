from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_NAME
from state import QueryPlan, Verdict
from prompts import PLAN_QUERIES_PROMPT, JUDGE_PROMPT
from llm_utils import ask_structured

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

# Test 1: planning queries
plan = ask_structured(
    llm,
    PLAN_QUERIES_PROMPT.format(topic="solid-state batteries", n=3),
    QueryPlan,
)
print("QUERIES:")
for q in plan.queries:
    print("-", q)

# Test 2: judging weak evidence (should say NOT enough)
verdict = ask_structured(
    llm,
    JUDGE_PROMPT.format(
        topic="solid-state batteries",
        sources="[1] Cooking tips - how to boil an egg",
    ),
    Verdict,
)
print("\nENOUGH?", verdict.is_enough)
print("REASON:", verdict.reason)