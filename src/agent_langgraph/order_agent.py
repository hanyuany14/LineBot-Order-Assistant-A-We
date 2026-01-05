import os
from datetime import datetime
from typing import Literal, TypedDict, Optional
from pydantic import BaseModel, Field
import json
from sqlalchemy import text

# LangChain / LangGraph imports
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

# DB & Toolkit imports
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.tools import tool

from src.utils import LLMUtils
from src.utils import PostgreUtils

llm = LLMUtils.GPT51_MINI_LLM_MODEL
query_tool = QuerySQLDatabaseTool(db=PostgreUtils.PG_DB)

from src.agent_langgraph.state import AgentState, OrderDetails


# ==========================================
# 3. 定義 Nodes (整合 Toolkit)
# ==========================================


def order_extraction_node(state: AgentState):
    """O1: 從對話中提取訂單資訊 (不變)"""
    print("--- [Order Agent] 提取訂單資訊 ---")
    last_message = state["messages"][-1]
    structured_llm = llm.with_structured_output(OrderDetails)
    order_data = structured_llm.invoke(last_message.content)
    return {"order_info": order_data}


def inventory_check_node(state: AgentState):
    """
    O2 & O3: 優化版庫存檢查
    優化策略：
    1. 跳過 list_tables 和 get_schema 步驟。
    2. 直接將 'products' 表的結構注入到 Prompt 中。
    3. 讓 LLM 專注於生成 SQL，並立即執行。
    """
    print("--- [Order Agent] 正在檢查 DB 庫存 (Fast Mode) ---")
    order = state["order_info"]
    if not order:
        return {"inventory_available": False}

    # 1. 【關鍵優化】直接獲取 products 表的 Schema
    # 這會回傳類似： "CREATE TABLE products (product_name TEXT, quantity INTEGER...)" 的字串
    # Agent 看到這個就不會去猜欄位名稱，也不用浪費時間查表
    product_schema = PostgreUtils.PG_DB.get_table_info(["products"])

    # 2. 定義一個針對性極強的 Prompt
    # 我們告訴它：這是表結構，請寫 SQL 查庫存，不要廢話
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是 Postgres SQL 專家。給定以下資料表 Schema，請撰寫 SQL 查詢。"),
            (
                "user",
                f"""
        【Schema 資訊】:
        {product_schema}

        【任務目標】:
        請查詢商品 '{order.product_name}' 的庫存數量 (quantity)。

        【限制】:
        1. 不需要檢查是否大於購買數量，只要回傳 SELECT 語句查出目前的 quantity 即可。
        2. 請只回傳 SQL 語句，不要 Markdown 格式 (```sql ... ```)，只要純文字。
        """,
            ),
        ]
    )

    # 3. 生成 SQL
    # 這裡我們不 Bind Tool，直接讓 LLM 吐出 SQL 字串，這樣最快
    response = llm.invoke(check_prompt.format_messages())
    generated_sql = response.content.strip().replace("```sql", "").replace("```", "").strip()

    print(f"🤖 Generated SQL: {generated_sql}")

    # 4. 執行查詢
    # 使用 QuerySQLDatabaseTool 來執行 (它會處理連線與 Error Catching)

    try:
        # tool_output 通常回傳字串格式的 list，例如 "[(10,)]" 或 "[]"
        tool_output = query_tool.invoke(generated_sql)
        print(f"📊 DB Query Result: {tool_output}")

        # 5. 解析結果 (Python 邏輯處理)
        # 因為 SQL 回傳的是純文字，我們做簡單的解析
        # 預期格式: "[(10,)]" (有庫存) 或 "" (查無此人)
        import ast

        # 嘗試將字串轉回 Python List
        try:
            result_list = ast.literal_eval(tool_output)
        except:
            # 如果回傳的是空字串或其他錯誤訊息
            result_list = []

        if result_list and isinstance(result_list, list) and len(result_list) > 0:
            # 取得庫存量
            stock_qty = result_list[0][0]
            print(f"   🔢 目前庫存: {stock_qty}, 需求: {order.quantity}")

            # 判斷庫存是否足夠
            is_available = int(stock_qty) >= order.quantity
        else:
            print(f"   ⚠️ 查無商品: {order.product_name}")
            is_available = False

    except Exception as e:
        print(f"❌ SQL Execution Error: {e}")
        is_available = False

    return {"inventory_available": is_available}


def create_order_node(state: AgentState):
    """
    O4: 建立訂單 (針對 Schema 修正版)
    - 使用 Transaction 原子性操作
    - 寫入 JSONB 格式
    - 處理保留字 "order"
    """
    print("--- [Order Agent] 庫存充足，執行交易寫入 ---")
    order = state["order_info"]

    if order is None:
        return {"final_output": "訂單資訊缺失，無法建立訂單。"}

    # 1. 準備要寫入 JSONB 的資料
    # 對應你的 Schema: order_info JSONB
    order_content = {
        "product_name": order.product_name,
        "quantity": order.quantity,
        "note": "Created by AI Agent",
    }
    order_json_str = json.dumps(order_content, ensure_ascii=False)

    # 2. 設定 Customer ID
    # 注意：你的 Schema 需要 customer_id。
    # 這裡暫時 hardcode 為 1 (對應你的 Seed Data)，實際應用需從 state['user_id'] 取得
    TEST_CUSTOMER_ID = 1

    try:
        # 使用 PostgreUtils 的 engine 開啟交易
        # 請確保 PostgreUtils.PG_DB._engine 是正確的 sqlalchemy engine 物件
        with PostgreUtils.PG_DB._engine.begin() as conn:

            # --- 步驟 A: 扣庫存 ---
            # 修正欄位名稱：name -> product_name, stock_quantity -> quantity
            update_sql = text(
                """
                UPDATE products
                SET quantity = quantity - :qty
                WHERE product_name = :name AND quantity >= :qty
            """
            )

            res = conn.execute(update_sql, {"qty": order.quantity, "name": order.product_name})

            # 檢查是否有更新到資料 (若 rowcount 為 0 表示庫存不足或商品不存在)
            if res.rowcount == 0:
                print(f"⚠️ 扣庫存失敗：商品 {order.product_name} 不存在或數量不足")
                raise Exception("庫存不足 (併發檢查失敗)")

            # --- 步驟 B: 寫入訂單 ---
            # 修正表名："order" (需加雙引號)
            # 修正欄位：直接寫入 customer_id 與 order_info (JSONB)
            insert_sql = text(
                """
                INSERT INTO "order" (customer_id, order_info, created_at)
                VALUES (:cid, :info, NOW())
            """
            )

            conn.execute(
                insert_sql,
                {
                    "cid": TEST_CUSTOMER_ID,
                    "info": order_json_str,  # 這裡傳入 JSON 字串，Postgres 會自動轉成 JSONB
                },
            )

        # 交易成功 (with block 結束自動 commit)
        return {"final_output": f"✅ 成功下單！商品：{order.product_name}，數量：{order.quantity}"}

    except Exception as e:
        print(f"❌ Transaction Error: {e}")
        # 這裡可以根據錯誤類型回傳更詳細的訊息
        if "庫存不足" in str(e):
            return {"final_output": "下單失敗：就在剛剛，庫存被搶光了！"}
        else:
            return {"final_output": "下單失敗：系統發生未預期的錯誤。"}


# 為了在 create_order_node 使用 text() 和 engine
from sqlalchemy import text


def order_fail_node(state: AgentState):
    return {"final_output": "抱歉，經查詢後發現庫存不足。"}


# ==========================================
# 4. 建立 Graph
# ==========================================
order_workflow = StateGraph(AgentState)
order_workflow.add_node("extract_info", order_extraction_node)
order_workflow.add_node("check_inventory", inventory_check_node)
order_workflow.add_node("create_order", create_order_node)
order_workflow.add_node("notify_fail", order_fail_node)

order_workflow.add_edge(START, "extract_info")
order_workflow.add_edge("extract_info", "check_inventory")


def route_inventory(state: AgentState):
    if state["inventory_available"]:
        return "create_order"
    return "notify_fail"


order_workflow.add_conditional_edges("check_inventory", route_inventory)
order_workflow.add_edge("create_order", END)
order_workflow.add_edge("notify_fail", END)

app = order_workflow.compile()

# # ==========================================
# # 5. 測試
# # ==========================================
# if __name__ == "__main__":
#     # Case: 買 2 個 apple
#     inputs = {"messages": [HumanMessage(content="我要買 2 個 apple")]}
#     result = order_app.invoke(inputs)
#     print(f"\n💡 最終回應: {result.get('final_output')}")
