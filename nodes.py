from datetime import date
from langchain_groq import ChatGroq
from tavily import TavilyClient

from config import GROQ_API_KEY, TAVILY_API_KEY, MODEL_NAME
from state import ResearchState, QueryPlan, Verdict
from prompts import (
    PLAN_QUERIES_PROMPT,
    JUDGE_PROMPT,
    REFINE_PROMPT,
    WRITE_REPORT_PROMPT,
)
from llm_utils import ask_structured

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

NUM_QUERIES = 3            # queries per round
RESULTS_PER_QUERY = 3      # web results per query
MAX_CHARS_PER_SOURCE = 800 # keeps prompts small and fast


def _today() -> str:
    """Tell the LLM today's date so it does not guess the year."""
    return f"Today's date is {date.today().strftime('%B %d, %Y')}.\n\n"


def format_sources(results: list) -> str:
    """Turn the results list into numbered text for the LLM."""
    if not results:
        return "No sources found."
    blocks = []
    for i, r in enumerate(results, start=1):
        text = r["content"][:MAX_CHARS_PER_SOURCE]
        blocks.append(f"[{i}] {r['title']} - {r['url']}\n{text}")
    return "\n\n".join(blocks)


# ---------- Node 1: plan ----------
def plan_queries(state: ResearchState) -> dict:
    prompt = _today() + PLAN_QUERIES_PROMPT.format(
        topic=state["topic"], n=NUM_QUERIES
    )
    plan = ask_structured(llm, prompt, QueryPlan)
    return {
        "queries": plan.queries[:NUM_QUERIES],
        "results": [],
        "loop_count": 0,
    }


# ---------- Node 2: search ----------
def search_web(state: ResearchState) -> dict:
    results = list(state["results"])
    seen_urls = {r["url"] for r in results}

    for query in state["queries"]:
        try:
            response = tavily.search(query, max_results=RESULTS_PER_QUERY)
        except Exception as e:
            print(f"  (search failed for '{query}': {e})")
            continue  # one bad search should not kill the whole run
        for item in response.get("results", []):
            if item["url"] in seen_urls:
                continue  # skip duplicates
            seen_urls.add(item["url"])
            results.append({
                "title": item.get("title", "Untitled"),
                "url": item["url"],
                "content": item.get("content", ""),
            })
    return {"results": results}


# ---------- Node 3: judge ----------
def check_evidence(state: ResearchState) -> dict:
    prompt = _today() + JUDGE_PROMPT.format(
        topic=state["topic"], sources=format_sources(state["results"])
    )
    verdict = ask_structured(llm, prompt, Verdict)
    return {"is_enough": verdict.is_enough, "reason": verdict.reason}


# ---------- Node 4: refine ----------
def refine_queries(state: ResearchState) -> dict:
    prompt = _today() + REFINE_PROMPT.format(
        topic=state["topic"],
        old_queries="\n".join(f"- {q}" for q in state["queries"]),
        reason=state["reason"],
        n=NUM_QUERIES,
    )
    plan = ask_structured(llm, prompt, QueryPlan)
    return {
        "queries": plan.queries[:NUM_QUERIES],
        "loop_count": state["loop_count"] + 1,
    }


# ---------- Node 5: write ----------
def write_report(state: ResearchState) -> dict:
    if not state["results"]:
        return {"report": "# No report\n\nNo sources were found for this topic."}
    prompt = _today() + WRITE_REPORT_PROMPT.format(
        topic=state["topic"], sources=format_sources(state["results"])
    )
    report = llm.invoke(prompt).content
    return {"report": report}