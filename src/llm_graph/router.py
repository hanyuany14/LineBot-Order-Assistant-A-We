# 這是一個 router，導流給 chat, order, none


from typing import Literal
from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import StrOutputParser

from src.utils import select_llm_model
from src.llm_agents.prompts import Prompts
from .state import AgentState


class JudgeSituationRouter:
    def __init__(self):
        self.situations_list = ["order", "chat", "none"]
        self.situation_judge_model = select_llm_model("gpt-3.5-turbo")

    def manager_router(self, state: AgentState) -> Literal["order", "chat", "none"]:
        """a module to monitor or judge whether need to call order process"""
        return self.__judge(state["messages"])

    def __judge(self, user_msg: str) -> Literal["order", "chat", "none"]:
        """a module to monitor or judge whether need to call order process"""

        print(f"收到來自顧客訊息: {user_msg}")

        situaation_judge_prompt_template = PromptTemplate(
            name="situaation_judge_prompt",
            template=Prompts.MonitorAgent.situaation_judge_prompt,
            input_variables=["user_msg"],
        )

        chain = situaation_judge_prompt_template | self.situation_judge_model | StrOutputParser()
        check_result = chain.invoke({"user_msg": user_msg})

        for situation in self.situations_list:
            if situation in check_result:
                return situation  # type: ignore
        return "none"


# -------------------------------------------------


# def router(state) -> Literal["call_tool", "__end__", "continue"]:
#     # This is the router
#     messages = state["messages"]
#     last_message = messages[-1]
#     if last_message.tool_calls:
#         # The previous agent is invoking a tool
#         return "call_tool"
#     if "FINAL ANSWER" in last_message.content:
#         # Any agent decided the work is done
#         return "__end__"
#     return "continue"
