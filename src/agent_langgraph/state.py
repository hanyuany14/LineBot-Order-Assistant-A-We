import os
from datetime import datetime
from typing import Literal, TypedDict, Optional
from pydantic import BaseModel, Field


class OrderDetails(BaseModel):
    product_name: str = Field(description="產品名稱")
    quantity: int = Field(description="購買數量")


class AgentState(TypedDict):
    messages: list  # 共用：對話紀錄
    order_info: Optional[OrderDetails]  # Order Subgraph 專用：訂單資訊
    inventory_available: Optional[bool]  # Order Subgraph 專用：庫存狀態
    final_output: Optional[str]  # 共用：最終回覆內容
    intent: Optional[str]  # Main Graph 專用：紀錄 Supervisor 的決策
