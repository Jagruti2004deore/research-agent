from typing import TypedDict, List, Dict
from pydantic import BaseModel, Field


class ResearchState(TypedDict):
    """The agent's notebook, passed from step to step."""
    topic: str            # what the user wants researched
    queries: List[str]    # search queries for the current round
    results: List[Dict]   # all search results collected so far
    loop_count: int       # how many times we have searched again
    is_enough: bool       # did the judge say the evidence is enough?
    reason: str           # why the judge said yes or no
    report: str           # the final report


class QueryPlan(BaseModel):
    """Form the LLM fills in when planning searches."""
    queries: List[str] = Field(description="Distinct web search queries")


class Verdict(BaseModel):
    """Form the LLM fills in when judging the evidence."""
    is_enough: bool = Field(description="True if the evidence is enough for a good report")
    reason: str = Field(description="One or two sentences explaining the decision")