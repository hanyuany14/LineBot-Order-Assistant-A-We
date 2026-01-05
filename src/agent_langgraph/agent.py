import sys
import os
from typing import Literal, TypedDict, Optional
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from src.utils import LLMUtils

# from src.agent_langgraph.order_agent import app as order_app
from src.agent_langgraph.state import AgentState

llm = LLMUtils.GPT_LLM_MODEL


# 用於 Supervisor 分類意圖的結構
class RouteDecision(BaseModel):
    next: Literal["chat", "order", "none"] = Field(
        description="下一步要執行的動作: chat(閒聊), order(訂購), none(無動作)"
    )


# ==========================================
# 2. 定義 Main Graph Nodes
# ==========================================


def supervisor_node(state: AgentState):
    """S: 意圖分類 (Router)"""
    print("\n--- [Supervisor] 分析意圖... ---")

    system_prompt = (
        "你是一個路由器。根據使用者的輸入判斷下一步。"
        "如果是想要購買商品、查詢庫存或下單，回傳 'order'。"
        "如果是閒聊、問候或非購買相關問題，回傳 'chat'。"
        "如果輸入無意義、亂碼或不想理會，回傳 'none'。"
    )

    # 組合 Prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    # 使用結構化輸出確保路由準確
    router = llm.with_structured_output(RouteDecision)
    decision = router.invoke(messages)

    print(f"🧐 意圖判斷結果: {decision.next}")

    # 【關鍵修改】將決策存入 State，這樣 conditional_edge 就可以直接讀取，不用再花錢 call LLM
    return {"intent": decision.next}


def chat_node(state: AgentState):
    """C: 一般閒聊 Agent"""
    print("--- [Chat Agent] 進行閒聊... ---")
    response = llm.invoke(state["messages"])
    return {"final_output": response.content}


def order_graph_wrapper(state: AgentState):
    """
    O: 呼叫 Order Subgraph
    LangGraph 允許我們直接 invoke 另一個 CompiledGraph。
    這會將父圖的 State 傳入子圖，執行完後將子圖的變更合併回父圖。
    """
    print("--- [Enter Order Subgraph] 進入訂單子流程 ---")

    # 直接調用從外部 import 進來的 order_app
    # result_state = order_app.invoke(state)
    result_state = result_state or {}

    # 回傳子圖執行的結果，這會自動 merge 回 Main Graph 的 state
    return result_state


def none_node(state: AgentState):
    """E1: 不做任何事"""
    print("--- [End Node] 無動作 ---")
    return {"final_output": "（系統忽略了您的訊息）"}


# ==========================================
# 3. 定義 Conditional Logic
# ==========================================


def route_supervisor(state: AgentState):
    """
    路由邏輯：直接讀取 Supervisor 存入 State 的 'intent'
    """
    intent = state.get("intent", "none")

    if intent == "chat":
        return "chat_agent"
    elif intent == "order":
        return "order_agent"
    else:
        return "no_action"


# ==========================================
# 4. 建立 Main Graph (主流程)
# ==========================================

main_workflow = StateGraph(AgentState)

# 新增節點
main_workflow.add_node("supervisor", supervisor_node)
main_workflow.add_node("chat_agent", chat_node)
main_workflow.add_node("order_agent", order_graph_wrapper)  # 這裡連接到子圖 Wrapper
main_workflow.add_node("no_action", none_node)

# 設定起點
main_workflow.add_edge(START, "supervisor")

# 設定條件分支
main_workflow.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {"chat_agent": "chat_agent", "order_agent": "order_agent", "no_action": "no_action"},
)

# 設定終點
main_workflow.add_edge("chat_agent", END)
main_workflow.add_edge("order_agent", END)
main_workflow.add_edge("no_action", END)

# 編譯主程式
app = main_workflow.compile()


# # ==========================================
# # 5. 測試執行
# # ==========================================


# def run_demo(user_input):
#     print(f"\n{'='*40}")
#     print(f"👤 User: {user_input}")

#     # 初始化 State
#     initial_state = {"messages": [HumanMessage(content=user_input)]}

#     try:
#         # 執行 Graph
#         result = app.invoke(initial_state)
#         print(f"🤖 System: {result.get('final_output')}")
#     except Exception as e:
#         print(f"❌ Error: {e}")


# if __name__ == "__main__":
#     # 測試 1: 閒聊 -> 走 Chat Node
#     run_demo("你好，請問你是誰？")

#     # 測試 2: 訂購 -> 走 Order Node (Subgraph) -> 檢查庫存 -> 下單
#     # (這會觸發你的 SQL Agent 邏輯)
#     run_demo("我要買 2 個 apple")

#     # 測試 3: 訂購失敗 -> 走 Order Node (Subgraph) -> 檢查庫存 -> 失敗
#     run_demo("幫我買 100 個 orange")

#     # 測試 4: 無意義
#     run_demo(".........")
