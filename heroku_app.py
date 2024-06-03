from flask import Flask, request, abort
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ImageMessage,
    VideoMessage,
    AudioMessage,
    LocationMessage,
    StickerMessage,
    FileMessage,
)
from src.configs import LineBotConfigs
from src.line.linebot_response import LineBot
from src.llm_agents.monitor_agent import MonitorAgent

line_bot_api = LineBotApi(LineBotConfigs.line_channel_access_token)
handler = WebhookHandler(LineBotConfigs.line_channel_secret)

app = Flask(__name__)


@app.route("/", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):

    situation = MonitorAgent().judge(event.message.text)
    print(f"店經理 Manager 判斷這是一個: '{situation}' 情境")

    if situation == "order":
        reply = LineBot().checking_stock_response(event)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif situation == "chat":
        reply = LineBot().chat_with_user_response(event)
        print(f"reply: {reply}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


@handler.add(
    MessageEvent,
    message=[
        ImageMessage,
        VideoMessage,
        AudioMessage,
        LocationMessage,
        StickerMessage,
        FileMessage,
    ],
)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text="阿偉看不懂，請輸入文字訊息喔～")
    )


if __name__ == "__main__":

    app.run()
