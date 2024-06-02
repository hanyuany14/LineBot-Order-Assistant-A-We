def get_order_success_reply(line_bot_chain, user_info_mapper) -> str:
    reply = f"""恭喜訂購成功，以下是你的訂單資訊：

訂單：
{line_bot_chain.order_data}

訂購人資訊
姓名：{user_info_mapper.get_user_name()}
年齡：{user_info_mapper.get_user_age()}
付款方式：{user_info_mapper.get_payment_method()}
送貨地址：{user_info_mapper.get_address()}

再次感謝您的訂購，歡迎再次光臨！
    """

    return reply
