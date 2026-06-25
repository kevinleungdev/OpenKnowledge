from typing import Any, Dict, List

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    Get the research topic from the messages.
    """
    # check if request has a history and combine the messages into a single string
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        research_topic = ""
        for m in messages:
            if isinstance(m, HumanMessage):
                research_topic += f"User: {m.content}\n"
            elif isinstance(m, AIMessage):
                research_topic += f"Assistant: {m.content}\n"
    return research_topic


def insert_citation_markers(text, citations_list):
    """
    Inserts citation markers into a text string based on start and end indices.

    Args:
        text (str): The original text string.
        citations_list (list): A list of dictionaries, where each dictionary
                               contains 'start_index', 'end_index', and
                               'segment_string' (the marker to insert).
                               Indices are assumed to be for the original text.

    Returns:
        str: The text with citation markers inserted
    """
    # Sort citations by end_index in descending order.
    # If `end_index` is the same, secondary sort by start_index descending.
    # This ensures that insertions at the end of the string don't affect
    # the indices of earlier parts of the string that still need to be processed.
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        # These indices refer to positions in the *original* text,
        # but since we iterate from the end, they remain valid for insertion
        # relative to the parts of the string already processed.
        end_idx = citation_info["end_index"]

        marker_to_insert = ""
        for segment in citation_info["segments"]:
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"

        # Insert the citation marker at the original `end_index` position
        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response):
    """ """
