import sys
from graph import graph

topic = " ".join(sys.argv[1:]) or "solid-state batteries"

initial_state = {
    "topic": topic,
    "queries": [],
    "results": [],
    "loop_count": 0,
    "is_enough": False,
    "reason": "",
    "report": "",
}

print(f"Researching: {topic}\n")
final_state = dict(initial_state)

# stream_mode="updates" shows each step as it finishes
for step in graph.stream(initial_state, stream_mode="updates"):
    for node_name, update in step.items():
        final_state.update(update)
        print(f"--> {node_name}")
        if node_name in ("plan_queries", "refine_queries"):
            for q in update["queries"]:
                print("     query:", q)
        elif node_name == "search_web":
            print("     total sources so far:", len(update["results"]))
        elif node_name == "check_evidence":
            print("     enough?", update["is_enough"], "|", update["reason"])

print("\n" + "=" * 60)
print(final_state["report"])

with open("report.md", "w", encoding="utf-8") as f:
    f.write(final_state["report"])
print("\nSaved report.md")