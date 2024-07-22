# Here is to define the Graph.

from langgraph.graph import END, StateGraph, START

from .state import AgentState
from .router import JudgeSituationRouter

workflow = StateGraph(AgentState)

workflow.set_entry_point("user")
workflow.add_node("order_agent", chart_node)
workflow.add_node("chat_agent", research_node)
# workflow.add_node("no_reply_agent", tool_node)

workflow.add_conditional_edges(
    source="user",
    path=JudgeSituationRouter().manager_router,
    path_map={"order": "order_agent", "chat": "chat_agent", "none": END},
)

graph = workflow.compile()


# -------------------------------------------------

workflow = StateGraph(AgentState)

workflow.add_node("Researcher", research_node)
workflow.add_node("chart_generator", chart_node)
workflow.add_node("call_tool", tool_node)

workflow.add_conditional_edges(
    "Researcher",
    router,
    {"continue": "chart_generator", "call_tool": "call_tool", "__end__": END},
)
workflow.add_conditional_edges(
    "chart_generator",
    router,
    {"continue": "Researcher", "call_tool": "call_tool", "__end__": END},
)

workflow.add_conditional_edges(
    "call_tool",
    # Each agent node updates the 'sender' field
    # the tool calling node does not, meaning
    # this edge will route back to the original agent
    # who invoked the tool
    lambda x: x["sender"],
    {
        "Researcher": "Researcher",
        "chart_generator": "chart_generator",
    },
)
workflow.add_edge(START, "Researcher")
graph = workflow.compile()
