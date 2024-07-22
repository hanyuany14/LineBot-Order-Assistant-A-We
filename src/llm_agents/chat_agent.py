from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSerializable


from src.utils import select_llm_model
from src.llm_agents.tools import get_current_menu
from src.llm_agents.prompts import Prompts


class ChatAgent:
    def __init__(self):
        # self.chat_model = select_llm_model("gpt-3.5-turbo")
        self.chat_model = select_llm_model("groq_llama_70b")

    def chat_with_user(self, user_msg: str) -> str:
        """The chatbot will chat with the user and return the response."""
        return self.make_chat_agent().invoke({"user_msg": user_msg})

    def make_chat_agent(self) -> RunnableSerializable:
        chat_prompt_template = PromptTemplate(
            name="chat_prompt",
            template=Prompts.ChatAgentPrompt.chat_prompt,
            input_variables=["user_msg"],
            partial_variables={"menu": get_current_menu()},
        )

        chat_prompt_template.pretty_print()

        return chat_prompt_template | self.chat_model | StrOutputParser()
