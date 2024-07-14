import json

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.configs import LineBotConfigs
from src.line.user_info import UserInfoMapping
from src.line.response_template import get_order_success_reply

from src.llm_agents.check_stock_agent import CheckStockAgent
from src.llm_agents.chat_agent import ChatAgent
from src.llm_agents.order_process_agent import OrderProcessAgent
from src.llm_agents.tools import get_current_menu


class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi(LineBotConfigs.line_channel_access_token)
        self.handler = WebhookHandler(LineBotConfigs.line_channel_secret)

    def default_response(self) -> str:
        return "Hello, world!"

    def checking_stock_response(self, event_dict: MessageEvent) -> str:

        check_agent = CheckStockAgent()
        msg_type = event_dict.message.type
        msg_text = event_dict.message.text

        if msg_type == "text" and event_dict.message.emojis is None:
            check_result = check_agent.check_inventory_process(msg_text)

            match check_result:
                case "Not enough":
                    menu = get_current_menu()
                    reply = f"你訂購的商品數量超過我們現有的庫存，你可以訂購少一點。\n以下是我們店內現有的商品：\n{menu}"

                case "Success":
                    order_process_result = OrderProcessAgent().save_order(check_agent.order_data)
                    print(f"order_process_result: {order_process_result}")

                    user_info_mapper = UserInfoMapping(event_dict.source.user_id)
                    reply = get_order_success_reply(check_agent, user_info_mapper)

                case _:
                    menu = get_current_menu()
                    reply = f"""阿偉不知道這個商品，或是訂購單之中有目前沒有的商品喔，請問清楚一點。\n以下是我們店內現有的商品：\n{menu}"""

        elif msg_type == "text" and event_dict.message.emojis:
            reply = "你傳的是表情符號呦～"
        else:
            reply = "你傳的不是文字呦～"

        return reply

    def chat_with_user_response(self, event_dict: MessageEvent) -> str:
        return ChatAgent().chat_with_user(event_dict.message.text)
