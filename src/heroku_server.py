from flask import Flask, request

import json

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from configs import LineBotConfigs

app = Flask(__name__)


@app.route("/", methods=["POST"])
def linebot():
    body = request.get_data(as_text=True)  # 取得收到的訊息內容
    try:
        json_data = json.loads(body)  # json 格式化訊息內容
        access_token = LineBotConfigs.line_channel_access_token
        secret = LineBotConfigs.line_channel_secret
        line_bot_api = LineBotApi(access_token)  # 確認 token 是否正確
        handler = WebhookHandler(secret)  # 確認 secret 是否正確
        signature = request.headers["X-Line-Signature"]  # 加入回傳的 headers
        handler.handle(body, signature)  # 綁定訊息回傳的相關資訊
        tk = json_data["events"][0]["replyToken"]  # 取得回傳訊息的 Token
        type = json_data["events"][0]["message"]["type"]  # 取得 LINe 收到的訊息類型
        if type == "text":
            msg = json_data["events"][0]["message"]["text"]  # 取得 LINE 收到的文字訊息
            print(msg)  # 印出內容
            reply = msg
        else:
            reply = "你傳的不是文字呦～"
        print(reply)
        line_bot_api.reply_message(tk, TextSendMessage(reply))  # 回傳訊息
    except:
        print(body)  # 如果發生錯誤，印出收到的內容
    return "OK"  # 驗證 Webhook 使用，不能省略


if __name__ == "__main__":

    app.run()
