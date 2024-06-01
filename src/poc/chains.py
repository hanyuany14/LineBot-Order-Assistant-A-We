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


class ChainsManager:
    def __init__(self):
        self.db = PostgreUtils.PG_DB
        self.covert_to_json_model = select_llm_model("gpt-3.5-turbo")
        self.check_sql_query_model = select_llm_model("gpt-3.5-turbo")
        self.check_inventory_model = select_llm_model("gpt-3.5-turbo")

    def main(self, user_msg: str) -> str | None:
        menu_list = self.__get_current_menu()
        print(f"menu: {menu_list}")

        json_data = self.convert_to_json_data(menu_list, user_msg)
        print(f"json_data: {json_data}")

        if json_data is None:
            return "Unknown product"

        query = self.get_checking_query(json_data)
        if "sql_query" in query:
            return self.check_inventory_status_in_db(query["sql_query"], json_data)
        return None

    def __get_current_menu(self) -> Any:
        menu = self.db.run_no_throw(
            "SELECT array_agg(product_name) FROM product WHERE is_delete = false;"
        )

        if type(menu) == str:
            menu_list = ast.literal_eval(menu)
            menu_list = menu_list[0][0]

        return menu_list

    def __check_unknown_product(self, d: dict | list) -> bool:
        if isinstance(d, dict):
            for key, value in d.items():
                if "Unknown product" in key or "Unknown product" in str(value):
                    return True
                if isinstance(value, (dict, list)):
                    if self.__check_unknown_product(value):
                        return True
        elif isinstance(d, list):
            for item in d:
                if "Unknown product" in str(item):
                    return True
                if isinstance(item, (dict, list)):
                    if self.__check_unknown_product(item):
                        return True
        return False

    def convert_to_json_data(
        self, menu_list: list, user_msg: str = "I want to order 2 apples."
    ) -> dict | None:
        """利用 LLM, 將用戶的消息轉換為json數據。"""

        class Order(BaseModel):
            product_name: str = Field(
                description="product name to be ordered. All product names are in lowercase and in singular form. For example, 'apple' instead of 'apples'. And it might be chinese or english."
            )
            quantity: int = Field(description="quantity of the item to be ordered")

        json_parser = JsonOutputParser(pydantic_object=Order)

        convert_to_json_prompt = """
        Transfer the order message into JSON format.{format_instructions}

        Here the infos you need:
        - The order message: {query}
        - The current menu in the shop: {menu}

        Here are the rules and format:
        - The order message can be in Chinese. If the product is in the current menu, translate it into English.
        - The order message can contain more than one product, so you can have multiple `product_name` and `quantity` pairs in the JSON data. Use a list format to include all the `product_name` and `quantity` pairs.
        - Pay attention to check if any ordered product in the order message is not in the current menu, if so, put "Unknown product" into the 'quantity' field.
        - Only include the `product_name` and `quantity` keys in the JSON data, do not include any other keys or information.

        Few-shot example:

        If the current menu is ["apple", "orange"]

        example1, "I want to order 2 apples and 10 oranges.", the JSON data should be:
        {few_shot_example}

        example2, "I want to order 2 apples and 10 guavas.", but the guava is not in the menu, then return:
        {unknown_product_few_shot_example}

        """

        convert_to_json_prompt_template = PromptTemplate(
            name="convert_to_json_data_prompt",
            template=convert_to_json_prompt,
            input_variables=["query"],
            partial_variables={
                "menu": menu_list,
                "format_instructions": json_parser.get_format_instructions(),
                # "few_shot_example": [
                #     {"product_name": "apple", "quantity": 2},
                #     {"product_name": "orange", "quantity": 10},
                # ],
                "unknown_product_few_shot_example": {
                    "product_name": ["apple", "guava"],
                    "quantity": [2, "Unknown product"],
                },
                "few_shot_example": {"product_name": ["apple", "orange"], "quantity": [2, 10]},
            },
        )

        convert_to_json_prompt_template.pretty_print()

        chain = convert_to_json_prompt_template | self.covert_to_json_model | json_parser
        response = chain.invoke({"query": user_msg})
        print(f"response: {response}")

        if "product_name" not in response or self.__check_unknown_product(response):
            return None

        return response

    def get_checking_query(self, json_data: dict) -> dict:
        """將 json 數據轉換為查詢字符串，查詢相關的訂單狀態"""

        _postgres_prompt = """
        You are a PostgreSQL expert. Given an input order data, first create a syntactically correct PostgreSQL query to run.
        Ensure that the condition is_delete = False is included.
        You can order the results to return the most informative data in the database.
        You have to Check all the products in the order data.
        Never query for all columns from a table. You must query only the columns that are needed to answer the query. Wrap each column name in double quotes (") to denote them as delimited identifiers.
        Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.

        Order Data in json: {json_data}

        Follow the rules and format below:
        1. Only give me the SQL query. Do not give me any other information.
        2. follow the format: {format_instructions}

        Only use the following tables:
        {table_info}

        Instruction: {input}
        """

        output_parser = StructuredOutputParser.from_response_schemas(
            response_schemas=[
                ResponseSchema(
                    name="sql_query", description="SQL query to answer the user's instruction."
                ),
            ]
        )

        checking_query_prompt_template = PromptTemplate(
            input_variables=["input", "table_info"],
            partial_variables={
                "json_data": json_data,
                "format_instructions": output_parser.get_format_instructions(),
            },
            template=_postgres_prompt,
            output_parser=output_parser,
        )

        chain = (
            checking_query_prompt_template
            | self.check_sql_query_model.bind(stop=["\nSQLResult:"])
            | output_parser
        )

        response = chain.invoke(
            {
                "input": "Create a query to find the inventory quantity of the product mentioned in the order data."
                + "\nSQLQuery:",
                "table_info": self.db.get_table_info(table_names=["inventory"]),
                "top_k": 10,
            }
        )

        checking_query_prompt = checking_query_prompt_template.invoke(
            {
                "input": "Create a query to find the inventory quantity of the product mentioned in the order data."
                + "\nSQLQuery:",
                "table_info": self.db.get_table_info(table_names=["inventory"]),
                "top_k": 10,
            }
        )
        print(f"checking_query_prompt: \n{checking_query_prompt}\n")
        print(f"\nSQL query: {response}\n")

        return response

    def check_inventory_status_in_db(self, check_query: str, json_data: dict) -> str:
        """查詢查詢庫存的 SQL 語法，並回傳訂單是否可以成功訂購"""

        check_prompt = PromptTemplate.from_template(
            template="""Given the following SQL query and SQL result, determine if each product in the order can be fulfilled based on the inventory quantity.

            Order Data: {json_data}
            SQL Query: {query}
            SQL Result: {result}
            Answer: Based on the inventory data, determine if each product in the order can be fulfilled.
            For each product, check if the inventory quantity is greater than or equal to the ordered quantity.
            If all products can be fulfilled, just return "Success."
            If any product cannot be fulfilled, just return "Not enough."

            Don't give me any other information. Just return "Success" or "Not enough."
            """,
            partial_variables={"json_data": json_data},
        )

        execute_query = QuerySQLDataBaseTool(db=self.db)

        chain = (
            RunnablePassthrough.assign(result=itemgetter("query") | execute_query)
            | check_prompt
            | self.check_inventory_model
            | StrOutputParser()
        )
        check_result = chain.invoke({"query": check_query})

        chain = RunnablePassthrough.assign(result=itemgetter("query") | execute_query)
        sql_result = chain.invoke({"query": check_query})
        print(f"sql execution results: {sql_result}")
        print(f"completed check_inventory_status_in_db: {check_result}")

        return check_result

    def insert_order_in_db(self, query: str) -> str:
        """by LLM"""
        ...

    def update_items_in_db(self, query: str) -> str:
        """by LLM"""
        ...
