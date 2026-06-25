from langchain import RunnableConfig
from langchain_openai import ChatOpenAI

from open_knowledge.agents.utils.schemas import Configuration, SearchQueryList
from open_knowledge.agents.utils.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from open_knowledge.agents.utils.utils import get_current_date, get_research_topic
from open_knowledge.agents.utils.prompts import (
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)


# Define nodes
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates search queries based on the User's question.

    Uses `deepseek-chat` to create an optimized search queries for web search based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including `search_query` key containing the generated queries
    """
    configurable = Configuration.from_runnable_config(config)

    # check for custom initial search count query
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # init deepseek-chat
    llm = ChatOpenAI(
        model=configurable.query_generator_model,
        temperature=1.3,
        max_retries=2,
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )

    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    return {"search_query": result.search_query}
