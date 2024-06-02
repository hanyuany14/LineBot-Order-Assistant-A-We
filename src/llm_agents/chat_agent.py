import re
import pandas as pd
import json
from io import BytesIO
from PIL import Image
import base64
import ast
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
from operator import itemgetter
from langchain.chains.sql_database.prompt import PROMPT, SQL_PROMPTS
from langchain_core.runnables import RunnableSerializable
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool

from src.llm_agents.check_stock_agent import CheckStockAgent
from src.utils import select_llm_model
from src.llm_agents.tools import get_current_menu


class ChatAgent:
    def __init__(self):
        self.chat_model = select_llm_model("gpt-3.5-turbo")

    def chat_with_user(self, user_msg: str) -> str:
        """The chatbot will chat with the user and return the response."""

        chat_prompt = """
        You are a bot in a LINE chatroom. The user sent the message: {user_msg}

        你的任務是判斷使用者的訊息並做出適當的回應。你可以在聊天中介紹店家和老闆的熱忱服務，回覆使用繁體中文。

        以下是我們的菜單和庫存：
        {menu}
        老闆對於每一位客人都非常熱忱，無論是第一次來訪的客人，還是老顧客，老闆總是親切地介紹產品，耐心地回答問題。希望每一位客人在這裡都能找到自己喜愛的產品，享受到最貼心的服務。


        請根據使用者的訊息做出簡單的回應，大約30~50字以內即可，並且可以帶到上述店家介紹和老闆熱忱的資訊。

        """

        chat_prompt_template = PromptTemplate(
            name="chat_prompt",
            template=chat_prompt,
            input_variables=["user_msg"],
            partial_variables={"menu": get_current_menu()},
        )
        chain = chat_prompt_template | self.chat_model | StrOutputParser()
        response = chain.invoke({"user_msg": user_msg})

        print(f"chat response: {response}")

        return response
