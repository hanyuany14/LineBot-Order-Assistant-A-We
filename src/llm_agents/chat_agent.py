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
from src.llm_agents.prompts import Prompts


class ChatAgent:
    def __init__(self):
        # self.chat_model = select_llm_model("gpt-3.5-turbo")
        self.chat_model = select_llm_model("groq_llama_70b")

    def chat_with_user(self, user_msg: str) -> str:
        """The chatbot will chat with the user and return the response."""

        chat_prompt_template = PromptTemplate(
            name="chat_prompt",
            template=Prompts.ChatAgentPrompt.chat_prompt,
            input_variables=["user_msg"],
            partial_variables={"menu": get_current_menu()},
        )

        chat_prompt_template.pretty_print()

        chain = chat_prompt_template | self.chat_model | StrOutputParser()
        response = chain.invoke({"user_msg": user_msg})

        return response
