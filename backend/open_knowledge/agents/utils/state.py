from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated


class OverallState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    search_query: Annotated[list, operator.add]
    web_search_result: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    initial_search_query_count: int
    max_research_loops: int
    research_loop_count: int
    reasoning_model: str


class ReflectionState(TypedDict):
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: Annotated[list[str], operator.add]
    research_loop_count: int
    number_of_ran_queries: int


class Query(TypedDict):
    query: str
    rationale: str


class QueryGenerationState(TypedDict):
    search_query: list[Query]


class WebSearchState(TypedDict):
    search_query: str
    id: str


@dataclass(kw_only=True)
class SearchStateOutput:
    running_summary: str = field(default=None)  # Final report
