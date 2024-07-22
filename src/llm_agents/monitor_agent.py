
from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import StrOutputParser

from src.utils import select_llm_model
from src.llm_agents.prompts import Prompts


class MonitorAgent:
    def __init__(self):
        self.situations_list = ["order", "chat", "none"]
        self.situation_judge_model = select_llm_model("gpt-3.5-turbo")

    def judge(self, user_msg: str) -> str:
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
                return situation
        return "none"
