from langchain.messages import AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END


def mock_llm(state: MessagesState):
    return {"messages": [AIMessage(content="greeting from a mock llm call")]}


# Create agent builder
agent_builder = StateGraph(MessagesState)

# Define nodes
agent_builder.add_node(mock_llm)
agent_builder.add_edge(START, "mock_llm")
agent_builder.add_edge("mock_llm", END)

# Compile mock agent
mock_agent = agent_builder.compile()
