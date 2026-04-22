from langchain.messages import AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END


def mock_llm(state: MessagesState):
    return {"messages": [AIMessage(content="greeting from a mock llm call")]}


# Create the Mock Agent Graph
builder = StateGraph(MessagesState)

# Define the nodes
builder.add_node(mock_llm)
builder.add_edge(START, "mock_llm")
builder.add_edge("mock_llm", END)

graph = builder.compile()
