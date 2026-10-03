from langgraph.graph import StateGraph, START, END

from state import ResearchState
from nodes import (
    plan_queries, search_web, check_evidence, refine_queries, write_report
)

MAX_LOOPS = 2  # how many times the agent may search again


def decide_next(state: ResearchState) -> str:
    """The decision point: write the report, or search again?"""
    if state["is_enough"]:
        return "write_report"
    if state["loop_count"] >= MAX_LOOPS:
        return "write_report"   # give up searching; write with what we have
    return "refine_queries"


def build_graph():
    builder = StateGraph(ResearchState)

    # 1. add the steps
    builder.add_node("plan_queries", plan_queries)
    builder.add_node("search_web", search_web)
    builder.add_node("check_evidence", check_evidence)
    builder.add_node("refine_queries", refine_queries)
    builder.add_node("write_report", write_report)

    # 2. connect them
    builder.add_edge(START, "plan_queries")
    builder.add_edge("plan_queries", "search_web")
    builder.add_edge("search_web", "check_evidence")

    # 3. the decision: one step, two possible next steps
    builder.add_conditional_edges(
        "check_evidence",
        decide_next,
        {"write_report": "write_report", "refine_queries": "refine_queries"},
    )

    # 4. the loop: refine goes back to search
    builder.add_edge("refine_queries", "search_web")
    builder.add_edge("write_report", END)

    return builder.compile()


graph = build_graph()