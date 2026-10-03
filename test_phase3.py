from nodes import (
    plan_queries, search_web, check_evidence, refine_queries, write_report
)

state = {
    "topic": "solid-state batteries",
    "queries": [],
    "results": [],
    "loop_count": 0,
    "is_enough": False,
    "reason": "",
    "report": "",
}


def run(name, fn):
    print(f"\n=== {name} ===")
    state.update(fn(state))


run("1. PLAN", plan_queries)
for q in state["queries"]:
    print("-", q)

run("2. SEARCH", search_web)
print("sources collected:", len(state["results"]))
for r in state["results"]:
    print("-", r["title"])

run("3. CHECK", check_evidence)
print("enough?", state["is_enough"])
print("reason:", state["reason"])

run("4. REFINE (just to test it)", refine_queries)
for q in state["queries"]:
    print("-", q)
print("loop_count:", state["loop_count"])

run("5. WRITE", write_report)
print(state["report"])