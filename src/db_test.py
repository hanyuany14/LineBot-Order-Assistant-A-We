import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

from configs import PostgreConfigs

DB_URI = PostgreConfigs.DB_ENGINE_CONNECT_STR


def run_query(sql_query):
    """
    通用函式：連接資料庫並執行 SQL
    """
    conn = None
    try:
        # 1. 建立連線
        conn = psycopg2.connect(DB_URI)

        # 2. 建立 Cursor (設定 cursor_factory 讓我們拿到的結果是 Dictionary 格式，比較好讀)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 3. 執行 SQL
        print(f"🔄 正在執行 SQL: {sql_query}")
        cur.execute(sql_query)

        # 4. 判斷是查詢還是寫入
        if sql_query.strip().upper().startswith("SELECT"):
            # 如果是查詢，回傳結果
            result = cur.fetchall()
            return result
        else:
            # 如果是 INSERT/UPDATE，提交變更 (Commit)
            conn.commit()
            return {"status": "success", "rows_affected": cur.rowcount}

    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        if conn:
            conn.rollback()  # 發生錯誤時回滾
        return None

    finally:
        # 5. 關閉連線
        if conn:
            cur.close()
            conn.close()


# ==========================================
# 模擬 Agent 的行為測試
# ==========================================

if __name__ == "__main__":

    # --- 情境 1: CheckStockAgent 想要查詢庫存 ---
    # 這是 Agent 可能生成的 SQL
    agent_select_sql = """
    SELECT product_name, quantity, price
    FROM products
    WHERE product_name IN ('apple', 'orange');
    """

    print("\n--- 測試 1: 查詢庫存 ---")
    stock_data = run_query(agent_select_sql)
    print("查詢結果:", json.dumps(stock_data, indent=2, ensure_ascii=False))

    # --- 情境 2: OrderProcessAgent 想要插入訂單 ---
    # 注意：這裡示範如何插入 JSONB 資料
    # Agent 生成的 SQL 會包含單引號，這就是為什麼我們需要 raw SQL 執行能力
    agent_insert_sql = """
    INSERT INTO "order" (customer_id, order_info)
    VALUES (1, '{"product_name": ["apple"], "order_quantity": [2]}'::jsonb);
    """

    print("\n--- 測試 2: 建立訂單 ---")
    insert_result = run_query(agent_insert_sql)
    print("寫入結果:", insert_result)

    # --- 情境 3: OrderProcessAgent 想要扣除庫存 ---
    agent_update_sql = """
    UPDATE products
    SET quantity = quantity - 2
    WHERE product_name = 'apple';
    """

    print("\n--- 測試 3: 更新庫存 ---")
    update_result = run_query(agent_update_sql)
    print("更新結果:", update_result)

    # --- 最後確認: 再次查詢看看 apple 數量是否變少 ---
    check_sql = "SELECT product_name, quantity FROM products WHERE product_name = 'apple';"
    final_check = run_query(check_sql)
    print("\n--- 最終檢查 ---")
    print(final_check)
