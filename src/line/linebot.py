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

# multi_emojis = {
#     "type": "message",
#     "mode": "active",
#     "timestamp": 1717268436435,
#     "source": {"type": "user", "userId": "U8c673b20a160a68f671d0cc94969ba55"},
#     "webhook_event_id": "01HZAJSNYD4NY0K9RSDQJTB89N",
#     "delivery_context": {"isRedelivery": false},
#     "reply_token": "d7d7150caa3b4c8d8be2aacd28a49a63",
#     "message": {
#         "emojis": [
#             {"emojiId": "025", "index": 0, "length": 7, "productId": "645314d6a377626a1179b30d"},
#             {"emojiId": "025", "index": 7, "length": 7, "productId": "645314d6a377626a1179b30d"},
#             {"emojiId": "025", "index": 14, "length": 7, "productId": "645314d6a377626a1179b30d"},
#             {"emojiId": "025", "index": 21, "length": 7, "productId": "645314d6a377626a1179b30d"},
#         ],
#         "id": "510760752903356497",
#         "text": "(emoji)(emoji)(emoji)(emoji)",
#         "type": "text",
#     },
# }


class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi(LineBotConfigs.line_channel_access_token)
        self.handler = WebhookHandler(LineBotConfigs.line_channel_secret)  # 確認 secret 是否正確

    def bot_response(self, event_dict: MessageEvent) -> str:
        return "Hello, world!"

    def linebot_response(self, event_dict: MessageEvent) -> str:

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
