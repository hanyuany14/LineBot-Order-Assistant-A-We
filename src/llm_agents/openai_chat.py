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

from utils import select_llm_model
from utils import PostgreUtils
from utils import LLMUtils


def openai_chat():

    # # 創建助理
    # assistant = LLMUtils.OPENAI_CLIENT.beta.assistants.create(
    #     name="Financial Analyst Assistant",
    #     instructions="You are an expert financial analyst. Use you knowledge base to answer questions about audited financial statements.",
    #     model="gpt-4o",
    #     tools=[{"type": "file_search"}],
    # )

    # 創建向量存儲
    vector_store = LLMUtils.OPENAI_CLIENT.beta.vector_stores.create(name="Financial Statements")

    # 準備文件上傳
    file_name = "src/docs/testing.pdf"
    file_paths = [file_name]
    file_streams = [open(path, "rb") for path in file_paths]
    print(file_streams)

    # 上傳文件並檢查狀態
    # try:
    file_batch = LLMUtils.OPENAI_CLIENT.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    print(file_batch.status)
    print(file_batch.file_counts)

    # except Exception as e:
    #     print(f"File upload failed: {e}")

    # # 更新助理
    # assistant = LLMUtils.OPENAI_CLIENT.beta.assistants.update(
    #     assistant_id=assistant.id,
    #     tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    # )

    # # 創建消息文件
    # try:
    #     message_file = LLMUtils.OPENAI_CLIENT.files.create(
    #         file=open(file_name, "rb"), purpose="assistants"
    #     )
    # except Exception as e:
    #     print(f"File creation failed: {e}")

    # # 創建對話線程並附加文件
    # try:
    #     thread = LLMUtils.OPENAI_CLIENT.beta.threads.create(
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": "summarize the file for me",
    #                 "attachments": [
    #                     {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
    #                 ],
    #             }
    #         ]
    #     )
    #     print(thread.tool_resources.file_search)

    # except Exception as e:
    #     print(f"Thread creation failed: {e}")

    # run = LLMUtils.OPENAI_CLIENT.beta.threads.runs.create_and_poll(
    #     thread_id=thread.id, assistant_id=assistant.id
    # )

    # messages = list(
    #     LLMUtils.OPENAI_CLIENT.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    # )

    # message_content = messages[0].content[0].text
    # annotations = message_content.annotations
    # citations = []
    # for index, annotation in enumerate(annotations):
    #     message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
    #     if file_citation := getattr(annotation, "file_citation", None):
    #         cited_file = LLMUtils.OPENAI_CLIENT.files.retrieve(file_citation.file_id)
    #         citations.append(f"[{index}] {cited_file.filename}")

    # print(message_content.value)
    # print("\n".join(citations))

    # return message_content.value
