from flask import Flask, request, abort
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.configs import LineBotConfigs
from src.line.linebot import LineBot

app = Flask(__name__)

access_token = LineBotConfigs.line_channel_access_token
secret = LineBotConfigs.line_channel_secret
line_bot_api = LineBotApi(access_token)  # 確認 token 是否正確
handler = WebhookHandler(secret)  # 確認 secret 是否正確


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
def handle_message(event):
    reply = LineBot().linebot_response(event)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


if __name__ == "__main__":

    app.run(debug=True)
