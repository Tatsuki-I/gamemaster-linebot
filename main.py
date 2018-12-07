from flask import Flask, request, abort
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

class Werewolf(object):
    def __init__(self):
        self.phase = "wait"
        self.user = []

class GameMember(object):
    def __init__(self, user_id):
        self.user_id = user_id
        self.job = ""
        self.isDead = False

werewolf = Werewolf()

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def werewolf_start(event):
    if werewolf.phase == "wait" and event.message.text == "/werewolf":
        werewolf.phase = "join"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="人狼ゲームを始めます。\nまずはじめに参加者を募ります。\n参加したい方は join と発言して下さい。\nまた、全員の参加が終了したら finish と発言して下さい。"))
    elif werewolf.phase == "join" and event.message.text == "join":
        if event.source.user_id in werewolf.user:
            werewolf.user.append(GameMember(event.source.user_id))
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="受け付けました。"))
        else:
            line_bot_api.reply_message(
            event.reply_token,
                TextSendMessage(text="あなたは既に受け付けています。"))




# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
