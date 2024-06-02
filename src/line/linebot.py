import json

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.configs import LineBotConfigs
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

multi_emojis = {
    "deliveryContext": {"isRedelivery": false},
    "message": {
        "emojis": [
            {"emojiId": "206", "index": 0, "length": 7, "productId": "5ac1bfd5040ab15980c9b435"}
        ],
        "id": "510833175011000437",
        "text": "(hijab)hjnnj",
        "type": "text",
    },
    "mode": "active",
    "replyToken": "1f5c1b1634df41ff9777d69aca0c6032",
    "source": {"type": "user", "userId": "U8c673b20a160a68f671d0cc94969ba55"},
    "timestamp": 1717311603550,
    "type": "message",
    "webhookEventId": "01HZBVZ1ATKWXFE5T08QC2QTS5",
}


class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi(LineBotConfigs.line_channel_access_token)
        self.handler = WebhookHandler(LineBotConfigs.line_channel_secret)  # 確認 secret 是否正確

    def default_response(self, event_dict: MessageEvent) -> str:
        return "Hello, world!"

    def checking_order_response(self, event_dict: MessageEvent) -> str:

        msg_type = event_dict.message.type
        msg_text = event_dict.message.text

        if msg_type == "text" and event_dict.message.emojis is None:
            check_result = ChainsManager().main(msg_text)
            reply = check_result if check_result else "我找不到呦～"

        elif msg_type == "text" and event_dict.message.emojis:
            reply = "你傳的是表情符號呦～"
        else:
            reply = "你傳的不是文字呦～"

        return reply
