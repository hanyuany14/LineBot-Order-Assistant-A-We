import re
import pandas as pd
import json
from io import BytesIO
from PIL import Image
import base64
import ast
from typing import Any
from sqlalchemy import text, bindparam

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
from langchain_core.tools import tool

from src.utils import select_llm_model
from src.utils import PostgreUtils
from src.exceptions import ValidationError
from src.llm_agents.tools import get_current_menu
from src.llm_agents.prompts import Prompts


class OrderProcessAgent:
    def __init__(self):
        self.db = PostgreUtils.PG_DB
        self.insert_order_model = select_llm_model("gpt-4o")
        self.update_inventory_order_model = select_llm_model("gpt-4o")

        self.execute_query = QuerySQLDataBaseTool(db=self.db)

    def save_order(self, json_data: dict | None):

        if json_data is not None:
            self.__insert_order_in_db(json_data)
            self.__update_inventory_in_db(json_data)
            return "The order has been successfully placed."
        return "The order is empty."

    def __insert_order_in_db(self, json_data: dict):
        """用於將訂單資料插入資料庫中。"""

        output_parser = StructuredOutputParser.from_response_schemas(
            response_schemas=[
                ResponseSchema(
                    name="sql_query", description="SQL query to answer the user's instruction."
                ),
            ]
        )

        insert_order_prompt_template = PromptTemplate(
            input_variables=["input", "table_info"],
            template=Prompts.OrderProcessAgentPrompt.insert_order_prompt,
            partial_variables={
                "json_data": json_data,
                "format_instructions": output_parser.get_format_instructions(),
                "customer_id": 1,
            },
            output_parser=output_parser,
        )

        chain = (
            insert_order_prompt_template
            | self.insert_order_model.bind(stop=["\nSQLResult:"])
            | output_parser
        )

        insert_query = chain.invoke(
            {
                "input": "Create a query to insert the order data into the database."
                + "\nSQLQuery:",
                "table_info": self.db.get_table_info(table_names=["order"]),
                "top_k": 10,
            }
        )
        print(f"\n新增 order 數據 SQL query:\n{insert_query}\n")

        if "sql_query" in insert_query:
            chain = RunnablePassthrough.assign(result=itemgetter("query") | self.execute_query)
            check_result = chain.invoke({"query": insert_query["sql_query"]})
            print(f"\n新增 order 數據結果為: \n{check_result}\n")
            return None

        raise ValidationError(
            "__insert_order_in_db error: The stock is insufficient. Please check the stock and try again."
        )

    def __update_inventory_in_db(self, json_data: dict):
        """根據 json_data 更新 inventory 表中的庫存。"""

        output_parser = StructuredOutputParser.from_response_schemas(
            response_schemas=[
                ResponseSchema(
                    name="sql_query", description="SQL query to answer the user's instruction."
                ),
            ]
        )

        update_inventory_prompt_template = PromptTemplate(
            input_variables=["input", "table_info"],
            template=Prompts.OrderProcessAgentPrompt.update_inventory_prompt,
            partial_variables={
                "json_data": json_data,
                "format_instructions": output_parser.get_format_instructions(),
            },
            output_parser=output_parser,
        )

        chain = (
            update_inventory_prompt_template
            | self.update_inventory_order_model.bind(stop=["\nSQLResult:"])
            | output_parser
        )
        update_query = chain.invoke(
            {
                "input": "Create queries to update the inventory quantity for each product in the order data."
                + "\nSQLQuery:",
                "table_info": self.db.get_table_info(table_names=["inventory"]),
                "top_k": 10,
            }
        )
        print(f"\n更新庫存 SQL query:\n{update_query}\n")

        if "sql_query" in update_query:
            chain = RunnablePassthrough.assign(result=itemgetter("query") | self.execute_query)
            check_result = chain.invoke({"query": update_query["sql_query"]})
            print(f"\n更新庫存: \n{check_result}\n")
            return None

        raise ValidationError(
            "__update_inventory_in_db error: The stock is insufficient. Please check the stock and try again."
        )
