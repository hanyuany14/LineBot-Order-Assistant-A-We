import ast
import re

from src.utils import PostgreUtils


def get_current_menu() -> dict:
    db = PostgreUtils.PG_DB

    query = """
        SELECT p.name AS product_name, p.price, i.quantity AS inventory_quantity
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE p.is_delete = false AND i.is_delete = false;
    """
    result = db.run(query)
    result_list = []
    if isinstance(result, str):
        if result == "":
            return {}
        try:
            result = re.sub(r"Decimal\('([\d\.]+)'\)", r"\1", result)
            result_list = ast.literal_eval(result)
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Error parsing result: {e}")
    else:
        result_list = result

    product_info_dict = {}
    for product_name, price, quantity in result_list:
        product_info_dict[product_name] = {"price": price, "quantity": quantity}

    return product_info_dict
