from flask import Flask, request, abort
import os
import random

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

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

class Werewolf(object):
    def __init__(self):
        self.phase = "wait"
        self.user_id = []
        self.job = {}
        self.done = {}
        self.dead = {}

    def add_user(self, user_id):
        self.user_id.append(user_id)
        self.job[user_id] = "citizen"
        self.done[user_id] = False
        self.dead[user_id] = False

    def reinit(self):
        self.phase = "wait"
        self.user_id = []
        self.job = {}
        self.done = {}
        self.dead = {}

werewolf = Werewolf()

jobss = { 2 : ["citizen", "werewolf"]
        , 3 : ["citizen", "citizen", "werewolf"]
        , 4 : ["citizen", "citizen", "seer", "werewolf"]
        , 5 : ["citizen", "citizen", "seer", "werewolf", "knight"]
        , 6 : ["citizen", "citizen", "seer", "werewolf", "knight", "madman"] }

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


@handler.add(MessageEvent, message = TextMessage)
def werewolf_start(event):
    if werewolf.phase == "wait" and "/werewolf" in event.message.text.lower():
        werewolf.phase = "join"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = "人狼ゲームを始めます。\nゲームを開始する前に、このbotを友達登録して下さい。\nはじめに参加者を募ります。\n参加したい方は join と発言して下さい。\nまた、全員の参加が終了したら finish と発言して下さい。\nゲームを強制終了したい場合は、 /end と発言して下さい。"))
    elif werewolf.phase == "join" and "join" in event.message.text.lower() and not event.source.user_id in werewolf.user_id:
        werewolf.add_user(event.source.user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = ("受け付けました。\nあなたのIDは" + str(len(werewolf.user_id)) + "です。")))
    elif werewolf.phase == "join" and "join" in event.message.text.lower() and event.source.user_id in werewolf.user_id:
            line_bot_api.reply_message(
            event.reply_token,
                TextSendMessage(text = "あなたは既に受け付けています。"))
    elif werewolf.phase == "join" and "finish" in event.message.text.lower():
        if len(werewolf.user_id) < 2:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text = "人数が足りません。"))
        else:
            werewolf.phase == "night"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "受け付けを締め切りました。"))
            jobs = random.sample(jobss[len(werewolf.user_id)], len(werewolf.user_id))
            for (uid, job) in zip(werewolf.user_id, jobs):
                werewolf.job[uid] = job
                night_act(uid, True)
    elif not werewolf.phase == "wait" and "/end" in event.message.text.lower():
        werewolf.reinit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = "ゲームを強制終了します。"))

def night_act(uid, is1st):
    if is1st:
        if werewolf.job[uid] == "citizen":
            werewolf.done[uid] = True
            line_bot_api.push_message(uid, TextSendMessage(text="あなたの役職は市民です。\n夜のアクションはありません。\n対面してゲームを行っている場合は、画面を操作するふりをして下さい。"))
        elif werewolf.job[uid] == "werewolf":
            line_bot_api.push_message(uid, TextSendMessage(text="あなたの役職は人狼です。\n夜のアクションを行います。\n殺したい相手のIDを入力して下さい。"))



if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
