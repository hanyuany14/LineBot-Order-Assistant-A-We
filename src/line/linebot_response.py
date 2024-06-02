import json

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.configs import LineBotConfigs
from src.line.user_info import UserInfoMapping
from src.line.response_template import get_order_success_reply
from src.poc.chains import ChainsManager

# event_dict = {
#     "type": "message",
#     "mode": "active",
#     "timestamp": 1717267790484,
#     "source": {"type": "user", "userId": "U8c673b20a160a68f671d0cc94969ba55"},
#     "webhook_event_id": "01HZAJ5Z4ENWDSG4GJKW30C18T",
#     "delivery_context": {"isRedelivery": false},
#     "reply_token": "f3605b2cdd73454798efec55c2cccd19",
#     "message": {
#         "emojis": [
#             {"emojiId": "027", "index": 0, "length": 7, "productId": "645314d6a377626a1179b30d"}
#         ],
#         "id": "510759669179088945",
#         "text": "(emoji)",
#         "type": "text",
#     },
# }

# multi_emojis = {
#     "deliveryContext": {"isRedelivery": false},
#     "message": {
#         "emojis": [
#             {"emojiId": "206", "index": 0, "length": 7, "productId": "5ac1bfd5040ab15980c9b435"}
#         ],
#         "id": "510833175011000437",
#         "text": "(hijab)hjnnj",
#         "type": "text",
#     },
#     "mode": "active",
#     "replyToken": "1f5c1b1634df41ff9777d69aca0c6032",
#     "source": {"type": "user", "userId": "U8c673b20a160a68f671d0cc94969ba55"},
#     "timestamp": 1717311603550,
#     "type": "message",
#     "webhookEventId": "01HZBVZ1ATKWXFE5T08QC2QTS5",
# }


class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi(LineBotConfigs.line_channel_access_token)
        self.handler = WebhookHandler(LineBotConfigs.line_channel_secret)
        self.line_bot_chain = ChainsManager()

    def default_response(self, event_dict: MessageEvent) -> str:
        return "Hello, world!"

    def checking_stock_response(self, event_dict: MessageEvent) -> str:

        msg_type = event_dict.message.type
        msg_text = event_dict.message.text

        if msg_type == "text" and event_dict.message.emojis is None:
            check_result = self.line_bot_chain.check_inventory_process(msg_text)

            match check_result:
                case "Unknown product":
                    menu = self.line_bot_chain.get_current_menu()
                    reply = f"""阿偉不知道這個商品，或是訂購單之中有目前沒有的商品喔，請問清楚一點。\n以下是我們店內現有的商品：\n{menu}"""

                case "Not enough":
                    reply = "你訂購的商品數量超過我們現有的庫存，你可以訂購少一點"
                    # TODO: 這裏可以讓 AI 回傳現有庫存的數量

                case "Success":
                    user_info_mapper = UserInfoMapping(event_dict.source.user_id)
                    reply = get_order_success_reply(self.line_bot_chain, user_info_mapper)

                case _:
                    reply = "阿偉現在好累不知道你在說啥"

        elif msg_type == "text" and event_dict.message.emojis:
            reply = "你傳的是表情符號呦～"
        else:
            reply = "你傳的不是文字呦～"

        return reply

    def chat_with_user_response(self, event_dict: MessageEvent) -> str:
        return self.line_bot_chain.chat_with_user(event_dict.message.text)
