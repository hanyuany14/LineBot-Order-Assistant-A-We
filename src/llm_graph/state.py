# Here is to define the State.


import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
)


def replace_message(original: str, new: str) -> str:
    return new


class AgentState(TypedDict):
    messages: Annotated[str, replace_message]


# -------------------------------------------------

# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool

# class AgentState(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], operator.add] # MyState 的 messages 宣告是 Annotated, 裡面掛著 function concat_lists
#     sender: str
