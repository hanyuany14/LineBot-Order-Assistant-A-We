import re
import pandas as pd
import json
from io import BytesIO
from PIL import Image
import base64

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

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from utils import select_llm_model
from utils import PostgreUtils


class ChainsManager:
    def __init__(self):
        self.db = PostgreUtils.PG_DB
        self.covert_to_json_model = select_llm_model("gpt-4o")
        self.check_sql_query_model = select_llm_model("gpt-4o")
        self.check_inventory_model = select_llm_model("gpt-4o")

    def main(self, user_msg: str) -> str:

        main_chain = (
            itemgetter("query")
            | RunnableLambda(self.convert_to_json_data)
            | RunnableLambda(self.get_checking_query)
            | RunnableLambda(self.check_inventory_status_in_db)
        )

        response = main_chain.invoke({"query": user_msg})
        return response

    def convert_to_json_data(self, user_msg: str = "I want to order 2 apples.") -> dict:
        """利用 LLM, 將用戶的消息轉換為json數據。"""

        class Order(BaseModel):
            product_name: str = Field(description="product name to be ordered")
            quantity: int = Field(description="quantity of the item to be ordered")

        json_parser = JsonOutputParser(pydantic_object=Order)

        convert_to_json_prompt = PromptTemplate(
            name="convert_to_json_data_prompt",
            template="Transfer the order message into json format.\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": json_parser.get_format_instructions()},
        )

        chain = convert_to_json_prompt | self.covert_to_json_model | json_parser
        response = chain.invoke({"query": user_msg})

        print(f"response: {response}")
        return response

    def get_checking_query(self, json_data: dict) -> str:
        """將 json 數據轉換為查詢字符串，查詢相關的訂單狀態"""

        _postgres_prompt = """
        You are a PostgreSQL expert. Given an input order data, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the inventory quantity of the product mentioned in the order data.
        Ensure that the condition is_delete = False is included.
        Unless the user specifies in the order data a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. You can order the results to return the most informative data in the database.
        Never query for all columns from a table. You must query only the columns that are needed to answer the query. Wrap each column name in double quotes (") to denote them as delimited identifiers.
        Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.

        Use the following format:

        Order Data in json: {json_data}
        SQLQuery: SQL Query to run
        SQLResult: Result of the SQLQuery
        Inventory Quantity: Final answer here

        Only use the following tables:
        {table_info}

        Instruction: {input}.
        """

        checking_query_prompt_template = PromptTemplate(
            input_variables=["input", "table_info", "top_k", "json_data"],
            template=_postgres_prompt,
        )

        write_query = create_sql_query_chain(
            llm=self.check_sql_query_model, db=self.db, prompt=checking_query_prompt_template, k=10
        )
        chain = checking_query_prompt_template | write_query | StrOutputParser()
        response = chain.invoke(
            {
                "input": "Create a query to find the inventory quantity of the product mentioned in the order data",
                "table_info": lambda x: self.db.get_table_info(table_names=["inventory"]),
                "top_k": 10,
                "json_data": json_data,
            }
        )
        print(f"response: {response}")
        return response

    def check_inventory_status_in_db(self, check_query: str) -> str:
        """查詢查詢庫存的 SQL 語法，並回傳訂單是否可以成功訂購"""

        # TODO: 要加入 json data 才可以比較
        # TODO: 生成 json data 那邊要確認每一個商品內容是包含在 menu 裡面的

        check_prompt = PromptTemplate.from_template(
            """Given the following SQL query and SQL result, determine if each product in the order can be fulfilled based on the inventory quantity.

            SQL Query: {query}
            SQL Result: {result}
            Answer: Based on the inventory data, determine if each product in the order can be fulfilled.
            For each product, check if the inventory quantity is greater than or equal to the ordered quantity.
            If all products can be fulfilled, just return "Success."
            If any product cannot be fulfilled, just return "Not enough."

            Don't give me any other information. Just return "Success" or "Not enough."
            """
        )

        execute_query = QuerySQLDataBaseTool(db=self.db)
        chain = (
            RunnablePassthrough.assign(result=itemgetter("query") | execute_query)
            | check_prompt
            | self.check_inventory_model
            | StrOutputParser()
        )
        check_result = chain.invoke({"query": check_query})

        print(f"check_result: {check_result}")
        return check_result

    def insert_order_in_db(self, query: str) -> str:
        """by LLM"""
        ...

    def update_items_in_db(self, query: str) -> str:
        """by LLM"""
        ...
