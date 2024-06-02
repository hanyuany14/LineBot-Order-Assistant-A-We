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
from langchain_core.runnables import RunnablePassthrough

from src.utils import select_llm_model
from src.utils import PostgreUtils


class MonitorAgent:
    def __init__(self):
        self.situations_list = ["order", "chat", "none"]
        self.situation_judge_model = select_llm_model("gpt-3.5-turbo")

    def judge(self, user_msg: str) -> str:
        """a module to monitor or judge whether need to call order process"""
        situaation_judge_prompt = """You are a bot in a LINE chatroom. The user send to the message is: {user_msg}.Your task is to judge the received messages and classify them into one of the following situations:\n1. order: When the user mentions ordering a product from the store.\n2. chat: When the user interacts with the store, such as asking questions or chatting.\n3. none: When the user's message is just interaction between users and not with the store. After determining the situation, return only one of the following strings: "order", "chat", "none". Do not include any additional information."""

        situaation_judge_prompt_template = PromptTemplate(
            name="situaation_judge_prompt",
            template=situaation_judge_prompt,
            input_variables=["user_msg"],
        )
        chain = situaation_judge_prompt_template | self.situation_judge_model | StrOutputParser()
        check_result = chain.invoke({"user_msg": user_msg})

        for situation in self.situations_list:
            if situation in check_result:
                return situation
        return "none"
