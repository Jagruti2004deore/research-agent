import re
import unicodedata
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
from llm_utils import ask_structured, ask_text

# max_retries=0: we handle rate-limit waiting ourselves in llm_utils.py
llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY, max_retries=0)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

NUM_QUERIES = 3             # queries per round
RESULTS_PER_QUERY = 3       # web results per query
MAX_CHARS_PER_SOURCE = 500  # keeps prompts small, avoids rate limits
MAX_WRITER_SOURCES = 15     # the writer only sees this many sources

# sites we never want as sources
EXCLUDE_DOMAINS = ["youtube.com", "facebook.com", "instagram.com",
                   "tiktok.com", "pinterest.com", "quora.com"]


# ---------- Helpers ----------
def _today() -> str:
    """Tell the LLM today's date so it does not guess the year."""
    return f"Today's date is {date.today().strftime('%B %d, %Y')}.\n\n"


def clean_text(text: str) -> str:
    """Fix odd invisible characters that glue words together."""
    # odd space types -> normal space
    text = "".join(" " if unicodedata.category(c) == "Zs" else c for c in text)
    # zero-width characters -> normal space
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", " ", text)
    # special hyphens and minus signs -> normal hyphen
    text = re.sub(r"[\u2010-\u2012\u2212]", "-", text)
    # collapse accidental double spaces inside sentences
    text = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", text)
    return text


def format_sources(results: list) -> str:
    """Turn the results list into numbered text for the LLM."""
    if not results:
        return "No sources found."
    blocks = []
    for i, r in enumerate(results, start=1):
        text = (r.get("content") or "")[:MAX_CHARS_PER_SOURCE]
        blocks.append(f"[{i}] {r['title']} - {r['url']}\n{text}")
    return "\n\n".join(blocks)


def build_sources_section(report: str, results: list) -> str:
    """Build the Sources list in code, so titles and URLs are always exact."""
    cited = sorted({
        int(n) for n in re.findall(r"\[(\d+)\]", report)
        if 0 < int(n) <= len(results)
    })
    if not cited:
        return ""
    lines = ["", "", "## Sources", ""]
    for n in cited:
        r = results[n - 1]
        lines.append(f"[{n}] {r['title']} - {r['url']}  ")
    return "\n".join(lines)


# ---------- Node 1: plan ----------
def plan_queries(state: ResearchState) -> dict:
    prompt = _today() + PLAN_QUERIES_PROMPT.format(
        topic=state["topic"], n=NUM_QUERIES
    )
    plan = ask_structured(llm, prompt, QueryPlan)
    queries = [q for q in plan.queries if q.strip()][:NUM_QUERIES]
    if not queries:
        queries = [state["topic"]]  # fallback: search the topic itself
    return {
        "queries": queries,
        "results": [],
        "loop_count": 0,
    }


# ---------- Node 2: search ----------
def search_web(state: ResearchState) -> dict:
    results = list(state["results"])
    seen_urls = {r["url"] for r in results}

    for query in state["queries"]:
        try:
            response = tavily.search(
                query,
                max_results=RESULTS_PER_QUERY,
                exclude_domains=EXCLUDE_DOMAINS,
            )
        except Exception as e:
            print(f"  (search failed for '{query}': {e})")
            continue  # one bad search should not kill the whole run

        for item in response.get("results", []):
            url = item.get("url")
            if not url or url in seen_urls:
                continue  # skip duplicates and broken items
            seen_urls.add(url)
            results.append({
                "title": item.get("title") or "Untitled",
                "url": url,
                "content": item.get("content") or "",
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
    queries = [q for q in plan.queries if q.strip()][:NUM_QUERIES]
    if not queries:
        queries = state["queries"]  # fallback: reuse the old ones
    return {
        "queries": queries,
        "loop_count": state["loop_count"] + 1,
    }


# ---------- Node 5: write ----------
def write_report(state: ResearchState) -> dict:
    if not state["results"]:
        return {"report": "# No report\n\nNo sources were found for this topic."}

    results = state["results"][:MAX_WRITER_SOURCES]

    if state["is_enough"]:
        coverage_note = ""
    else:
        coverage_note = (
            "IMPORTANT: A reviewer decided the sources do NOT adequately cover "
            f"this topic. Reason: {state['reason']}\n"
            "Your summary must begin by saying this plainly. Include a finding "
            "only if a source directly states it about the exact subject of the "
            "topic, not a broader or neighboring subject. If no source does, say "
            "that no relevant findings were found and keep Key Findings to one "
            "bullet saying so.\n"
        )

    prompt = _today() + WRITE_REPORT_PROMPT.format(
        topic=state["topic"],
        coverage_note=coverage_note,
        sources=format_sources(results),
    )
    try:
        body = clean_text(ask_text(llm, prompt))
        report = body + build_sources_section(body, results)
    except Exception as e:
        report = f"# Report failed\n\nThe writer step hit an error: {e}"
    return {"report": report}