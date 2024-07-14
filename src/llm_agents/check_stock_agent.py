import re
import pandas as pd
import json
import ast
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from operator import itemgetter
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter
from langchain.chains.sql_database.prompt import PROMPT, SQL_PROMPTS
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.utils import select_llm_model
from src.utils import PostgreUtils
from src.exceptions import ValidationError
from src.llm_agents.prompts import Prompts


class CheckStockAgent:
    def __init__(self):
        self.db = PostgreUtils.PG_DB

        self.covert_to_json_model = select_llm_model("gpt-4o")
        self.check_sql_query_model = select_llm_model("gpt-3.5-turbo")
        self.check_inventory_model = select_llm_model("gpt-3.5-turbo")

        self.json_data = {"product_name": None, "order_quantity": None}

    @property
    def order_data(self) -> dict | None:
        return self.json_data

    def check_inventory_process(self, user_msg: str) -> str | None:
        """the function is used to check the inventory status of the products mentioned in the user's message.

        Args:
            user_msg (str):

        Returns:
            str | None: _description_
        """

        menu_list = self.get_current_prodcts()
        print(f"menu: {menu_list}")

        self.json_data = self.__convert_to_json_data(menu_list, user_msg)
        print(f"結構化的的訂單 json: \n{self.json_data}")

        try:
            self.__json_data_checker(self.json_data)
        except ValidationError as e:
            return str(e)

        query = self.__get_checking_query(self.json_data)
        if "sql_query" in query:
            return self.__check_inventory_status_in_db(query["sql_query"], self.json_data)

        return None

    def get_current_prodcts(self) -> Any:
        menu = self.db.run_no_throw("SELECT array_agg(name) FROM products WHERE is_delete = false;")
        if type(menu) == str:
            menu_list = ast.literal_eval(menu)
            menu_list = menu_list[0][0]

        return menu_list

    def __convert_to_json_data(
        self, menu_list: list, user_msg: str = "I want to order 2 apples."
    ) -> dict:
        """利用 LLM, 將用戶的消息轉換為json數據。"""

        class Order(BaseModel):
            product_name: list[str] = Field(
                description="product name to be ordered. All product names are in lowercase and in singular form. For example, 'apple' instead of 'apples'. And it might be chinese or english."
            )
            order_quantity: list[int] = Field(description="quantity of the item to be ordered")

        json_parser = JsonOutputParser(pydantic_object=Order)

        convert_to_json_prompt_template = PromptTemplate(
            name="convert_to_json_data_prompt",
            template=Prompts.CheckStockAgentPrompt.convert_to_json_prompt,
            input_variables=["query"],
            partial_variables={
                "menu": menu_list,
                "format_instructions": json_parser.get_format_instructions(),
            },
        )

        # convert_to_json_prompt_template.pretty_print()
        chain = convert_to_json_prompt_template | self.covert_to_json_model | json_parser
        response = chain.invoke({"query": user_msg})

        return response

    def __get_checking_query(self, json_data: dict) -> dict:
        """將 json 數據轉換為查詢字符串，查詢相關的訂單狀態"""

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
            template=Prompts.CheckStockAgentPrompt.postgres_prompt,
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
                "table_info": self.db.get_table_info(table_names=["products", "inventory"]),
                "top_k": 10,
            }
        )

        # checking_query_prompt = checking_query_prompt_template.invoke(
        #     {
        #         "input": "Create a query to find the inventory quantity of the product mentioned in the order data."
        #         + "\nSQLQuery:",
        #         "table_info": self.db.get_table_info(table_names=["inventory"]),
        #         "top_k": 10,
        #     }
        # )
        # print(f"checking_query_prompt: \n\n{checking_query_prompt}\n\n")
        print(f"\nSQL query: {response}\n")

        return response

    def __check_inventory_status_in_db(self, check_query: str, json_data: dict) -> str:
        """查詢查詢庫存的 SQL 語法，並回傳訂單是否可以成功訂購"""

        check_prompt = PromptTemplate.from_template(
            template=Prompts.CheckStockAgentPrompt.check_stock_prompt,
            partial_variables={"json_data": json_data},
        )

        execute_query = QuerySQLDataBaseTool(db=self.db)

        chain = RunnablePassthrough.assign(result=itemgetter("query") | execute_query)

        sql_result = chain.invoke({"query": check_query})
        print(f"SQL 查詢的原始結果為: {sql_result['result']}")

        chain = (
            RunnablePassthrough.assign(result=itemgetter("query") | execute_query)
            | check_prompt
            | self.check_inventory_model
            | StrOutputParser()
        )
        check_result = chain.invoke({"query": check_query})

        print(f"檢查結果判讀為: {check_result}")

        return check_result

    def __json_data_checker(self, json_data: dict):
        """用於檢查 json_data 的合法性。"""
        # 1. 檢查 dict 格式: dict, keys = ["product_name", "order_quantity"], values = [list, list]
        if not isinstance(json_data, dict):
            raise ValidationError("Invalid data format: json_data should be a dictionary.")
        if "product_name" not in json_data or "order_quantity" not in json_data:
            raise ValidationError(
                'Missing keys: json_data should contain "product_name" and "order_quantity".'
            )
        if not isinstance(json_data["product_name"], list) or not isinstance(
            json_data["order_quantity"], list
        ):
            raise ValidationError(
                'Invalid data types: "product_name" and "order_quantity" should be lists.'
            )

        product_names = json_data["product_name"]
        quantities = json_data["order_quantity"]

        if len(product_names) != len(quantities):
            raise ValidationError(
                'Mismatched lengths: "product_name" and "order_quantity" lists should have the same length.'
            )

        # 2. 檢查 product_name 是否不為 "Unknown product" 且存在於資料庫中
        for name in product_names:
            if name == "Unknown product":
                raise ValidationError('Invalid product: "product_name" contains "Unknown product".')

        # 3. 檢查 order_quantity 是否大於 0
        for order_quantity in quantities:
            if not isinstance(order_quantity, (int, float)) or order_quantity <= 0:
                raise ValidationError(
                    "Invalid order_quantity: all quantities should be greater than 0."
                )

        return "Valid data."
