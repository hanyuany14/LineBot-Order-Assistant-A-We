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
from src.line.linebot import LineBot
from src.poc.chains import ChainsManager


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

    # todo: 加入一個 AI 可以自主監聽是不是有人要訂單，否則直接回傳掰掰

    line_bot_chain = ChainsManager()
    reply = LineBot(line_bot_chain).checking_order_response(event)
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
