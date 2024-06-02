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
from src.exceptions import ValidationError


class CheckStockAgent:
    def __init__(self):
        self.db = PostgreUtils.PG_DB

        self.covert_to_json_model = select_llm_model("gpt-3.5-turbo")
        self.check_sql_query_model = select_llm_model("gpt-3.5-turbo")
        self.check_inventory_model = select_llm_model("gpt-3.5-turbo")

        self.json_data = {"product_name": None, "quantity": None}

    @property
    def order_data(self) -> dict | None:
        print(f"order_data: {self.json_data}")
        return self.json_data

    def check_inventory_process(self, user_msg: str) -> str | None:
        menu_list = self.get_current_prodcts()
        print(f"menu: {menu_list}")

        self.json_data = self.__convert_to_json_data(menu_list, user_msg)
        print(f"json_data: {self.json_data}")

        try:
            self.__json_data_checker(self.json_data)
        except ValidationError as e:
            return str(e)

        query = self.__get_checking_query(self.json_data)
        if "sql_query" in query:
            return self.__check_inventory_status_in_db(query["sql_query"], self.json_data)

        return None

    def get_current_prodcts(self) -> Any:
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

    def __convert_to_json_data(
        self, menu_list: list, user_msg: str = "I want to order 2 apples."
    ) -> dict:
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
        - The menu of the shop: {menu}

        Return the result in the following JSON format:
        {multiple_format_example}

        Here are the rules and format:
        - The order message can be in Chinese. If the product is in the current menu, translate it into English.
        - Pay attention to check if any ordered product in the order message is not in the current menu, if so, put "Unknown product" into the 'quantity' field.
        - Only include the `product_name` and `quantity` keys in the JSON data, do not include any other keys or information.

        Few-shot example:

        If the menu is ["apple", "orange"]

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
                "multiple_format_example": {
                    "product_name": ["item1", "item2"],
                    "quantity": ["quantity1", "quantity2"],
                },
                "unknown_product_few_shot_example": {
                    "product_name": ["apple", "guava"],
                    "quantity": [2, "Unknown product"],
                },
                "few_shot_example": {"product_name": ["apple", "orange"], "quantity": [2, 10]},
            },
        )

        # convert_to_json_prompt_template.pretty_print()
        chain = convert_to_json_prompt_template | self.covert_to_json_model | json_parser
        response = chain.invoke({"query": user_msg})

        return response

    def __get_checking_query(self, json_data: dict) -> dict:
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

        # checking_query_prompt = checking_query_prompt_template.invoke(
        #     {
        #         "input": "Create a query to find the inventory quantity of the product mentioned in the order data."
        #         + "\nSQLQuery:",
        #         "table_info": self.db.get_table_info(table_names=["inventory"]),
        #         "top_k": 10,
        #     }
        # )
        # print(f"checking_query_prompt: \n{checking_query_prompt}\n")
        print(f"\nSQL query: {response}\n")

        return response

    def __check_inventory_status_in_db(self, check_query: str, json_data: dict) -> str:
        """查詢查詢庫存的 SQL 語法，並回傳訂單是否可以成功訂購"""

        check_prompt = PromptTemplate.from_template(
            template="""Given the following SQL query and SQL result, determine if each product in the order can be fulfilled based on the inventory quantity.

            Order Data: {json_data}
            SQL Query: {query}
            SQL Result: {result}
            Answer: Based on the inventory data, determine if each product in the order can be fulfilled.
            For each product, check if the inventory quantity is greater than or equal to the ordered quantity.
            If all products can be fulfilled, just return "Success."
            If any product cannot be fulfilled, just return "Not enough"

            Don't give me any other information. Just return "Success" or "Not enough"
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
        print(f"completed __check_inventory_status_in_db: {check_result}")

        return check_result

    def __json_data_checker(self, json_data: dict):
        """用於檢查 json_data 的合法性。"""
        # 1. 檢查 dict 格式: dict, keys = ["product_name", "quantity"], values = [list, list]
        if not isinstance(json_data, dict):
            raise ValidationError("Invalid data format: json_data should be a dictionary.")
        if "product_name" not in json_data or "quantity" not in json_data:
            raise ValidationError(
                'Missing keys: json_data should contain "product_name" and "quantity".'
            )
        if not isinstance(json_data["product_name"], list) or not isinstance(
            json_data["quantity"], list
        ):
            raise ValidationError(
                'Invalid data types: "product_name" and "quantity" should be lists.'
            )

        product_names = json_data["product_name"]
        quantities = json_data["quantity"]

        if len(product_names) != len(quantities):
            raise ValidationError(
                'Mismatched lengths: "product_name" and "quantity" lists should have the same length.'
            )

        # 2. 檢查 product_name 是否不為 "Unknown product" 且存在於資料庫中
        for name in product_names:
            if name == "Unknown product":
                raise ValidationError('Invalid product: "product_name" contains "Unknown product".')

            result = self.db.run(
                command=f"SELECT COUNT(*) FROM \"product\" WHERE product_name = '{name}' AND is_delete = false;"
            )

            result_list = ast.literal_eval(str(result))

            if int(result_list[0][0]) == 0:
                raise ValidationError(f'Invalid product: "{name}" does not exist in the database.')

        # 3. 檢查 quantity 是否大於 0
        for quantity in quantities:
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                raise ValidationError("Invalid quantity: all quantities should be greater than 0.")

        # 4. 檢查資料庫中是否有足夠的商品庫存
        for name, quantity in zip(product_names, quantities):
            stock_check_query = f"""
                SELECT i.quantity
                FROM inventory i
                JOIN product p ON i.product_id = p.id
                WHERE p.product_name = '{name}' AND i.is_delete = false
            """
            result = self.db.run(command=stock_check_query)
            result_list = ast.literal_eval(str(result))
            stock = result_list[0][0]

            if stock is None or stock < quantity:
                raise ValidationError(f'Insufficient stock: "{name}" does not have enough stock.')

        return "Valid data."
