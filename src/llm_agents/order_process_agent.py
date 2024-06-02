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


class OrderProcessAgent:
    def __init__(self):
        self.db = PostgreUtils.PG_DB

    def save_order(self, json_data: dict):
        self.__insert_order_in_db(json_data)
        self.__update_inventory(json_data)

    def __insert_order_in_db(self, json_data: dict):
        """用於將訂單資料插入資料庫中。"""

        order_info_json = json.dumps(json_data)
        customer_id = 1

        query = f"INSERT INTO \"order\" (order_info, customer_id) VALUES ('{order_info_json}'::jsonb, {customer_id})"
        self.db.run(command=query)

    def __update_inventory(self, json_data: dict):
        """根據 json_data 更新 inventory 表中的庫存。"""

        product_names = json_data["product_name"]
        quantities = json_data["quantity"]

        for name, quantity in zip(product_names, quantities):
            update_query = f"""
                UPDATE "inventory"
                SET quantity = quantity - {quantity}
                WHERE product_id = (
                    SELECT id FROM "product" WHERE product_name = '{name}'
                ) AND is_delete = false
            """
            self.db.run(command=update_query)
