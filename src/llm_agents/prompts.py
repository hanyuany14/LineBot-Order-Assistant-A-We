class Prompts:
    class MonitorAgent:
        situaation_judge_prompt = """
You are a bot in a LINE chatroom. The user send to the message is: {user_msg}.
Your task is to judge the received messages and classify them into one of the following situations:
1. order: When the user mentions ordering a product from the store.
2. chat: When the user interacts with the store, such as asking questions or chatting about the store.
3. none: When the user's message is not relative with the store.
After determining the situation, return only one of the following strings: "order", "chat", "none".
Do not include any additional information.
"""

    class ChatAgentPrompt:
        chat_prompt = """
You are an assistant in a shop. The customer sent the message: {user_msg}

Your task is to determine the customer's message and respond simply, based on the information below, in about 30-50 words.

-
Here is our menu, including product names, prices, and available stock: {menu}
-
Please respond to the user based on the following information:
The owner is very enthusiastic about every customer, whether they are visiting for the first time or are regulars. The owner always warmly introduces products and patiently answers questions.
We hope every customer can find their favorite products here and enjoy the most attentive service.
Business hours are from 9 AM to 8 PM every day.
The address is: No. 1, Shifu Rd., Xinyi District, Taipei City.
The owner's name is Mr. Wang.
-
You must respond in Traditional Chinese.
You can introduce the shop information you know, but "respond based on the provided information above, avoiding making up any content."
If you don't know, simply respond with "I don't know this information."
    """

    class CheckStockAgentPrompt:

        convert_to_json_prompt = """
Transfer the order message into JSON format.{format_instructions}

Here the infos you need:
- The order message: {query}
- The menu of the shop: {menu}

Return the result in the following JSON format:
{{"product_name": ["item1"],"order_quantity": ["order_quantity1"]}}

or if the number of products is more than 2:
{{"product_name": ["item1", "item2", ...],"order_quantity": ["order_quantity1", "order_quantity2", ...]}}

Here are the rules and format:
- The order message can be in Chinese. If the product is in the Chinese or other language, translate it into English.
- Please pay attention to the products listed in the menu, as they might be in a different language than the products mentioned in the order message. Match the customer's ordered products to the products available in the menu and use the names from the menu as the output in the JSON data. If any ordered product is not found in the current menu, translate the product name into English, place it in the 'product_name' field, and set the 'order_quantity' field to "Unknown product."
- Only include the `product_name` and `order_quantity` keys in the JSON data, do not include any other keys or information.

Few-shot example:

If the menu now is ["apple", "orange"]

example1, "I want to order 2 apples.", the JSON data should be:
{{"product_name": ["apple"], "order_quantity": [2]}}

example2, "I want to order 2 papaya.", but the papaya 木瓜 is not in the menu, the JSON data should be:
{{"product_name": ["papaya"],"order_quantity": ["Unknown product"]}}

example3, "我要兩個頻果和3個芭樂", but the guava 芭樂 is not in the menu, then return:
{{"product_name": ["apple", "guava"],"order_quantity": [2, "Unknown product"]}}

example4, "我要5個桃子和一個瓶子", but the peach 桃子 and bottle 瓶子 are not in the menu, then return:
{{"product_name": ["peach", "bottle"],"order_quantity": ["Unknown product", "Unknown product"]}}

example5, "我要買一些餅乾和一個瓶子和14個蘋果", but the cookies 餅乾 and papaya 番木瓜 are not in the menu, then return:
{{"product_name": ["cookies", "bottle", "apple", "papaya"],"order_quantity": ["Unknown product", "Unknown product", 14, "Unknown product"]}}

example6, "我要買3份橘子和一些蘋果", but the order_quantity of apple is unknown even is in the menu, then return:
{{"product_name": ["apple", "orange"],"order_quantity": ["Unknown", 3]}}
"""

        postgres_prompt = """
You are a PostgreSQL expert. Given an input order data, first create a syntactically correct PostgreSQL query to run.
When encountering a string containing single quotes in SQL queries, such as \'gidle\'s album\', use two single quotes to escape the single quote within the string to avoid syntax errors. For example, \'gidle\'\'s album\'.
You can order the results to return the most informative data in the database.
You have to Check all the products in the order data.
Never query for all columns from a table. You must query only the columns that are needed to answer the query. Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.

Order data: {json_data}

Follow the rules and format below:
1. Only give me the SQL query. Do not give me any other information.
2. follow the format: {format_instructions}

Only use the following tables:
{table_info}

Instruction: {input}."""

        check_stock_prompt = """Given the SQL query and the corresponding SQL result, determine if the inventory has sufficient quantity to fulfill each product in the order.

Order: {json_data}

SQL Query: {query}
(The query retrieves the inventory quantity for the products needed in the order.)

SQL Result: {result}
(This is the result of the query showing the available inventory quantities. The sequence of the products in the result should match the sequence of the products in the order.)

Instructions:
1. Check if the inventory quantity is sufficient for each product listed in the "Order".
2. If all products can be fulfilled based on the inventory data, return "Success".
3. If any product cannot be fulfilled due to insufficient inventory, return "Not enough".

Return only "Success" or "Not enough"."""

    class OrderProcessAgentPrompt:
        insert_order_prompt = """
You are a PostgreSQL expert. Given an input order data, create a syntactically correct PostgreSQL INSERT query to run.
When encountering a string containing single quotes in SQL queries, such as \'gidle\'s album\', use two single quotes to escape the single quote within the string to avoid syntax errors. For example, \'gidle\'\'s album\'.
Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to the data type of the columns. If the column is of type json, you need to insert the data in json format. for example, INSERT INTO "order" (order_info, customer_id) VALUES ('{{order_info_json}}'::jsonb, 1)

Order Data in json: {json_data}

Follow the rules and format below:
1. Only give me the SQL query. Do not give me any other information.
2. follow the format: {format_instructions}

Only use the following tables:
{table_info}

Instruction: Insert the new order data into the database.
"""

        update_inventory_prompt = """
You are a PostgreSQL expert. Given an input order data, create syntactically correct PostgreSQL UPDATE queries to run.
Your task is to update the inventory quantity for each product in the order data.
When encountering a string containing single quotes in SQL queries, such as \'gidle\'s album\', use two single quotes to escape the single quote within the string to avoid syntax errors. For example, \'gidle\'\'s album\'.
Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.

Order Data in json: {json_data}

Follow the rules and format below:
1. Only give me the SQL queries. Do not give me any other information.
2. Use the format: {format_instructions}

Only use the following tables:
{table_info}

Instruction: Update the inventory data in the database based on the input order data.
"""
