from datetime import datetime
import os
import utils.my_func as my_func
from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from handler.msg_handler import MSG_HANDLER
from handler.cmd_handler import CMD_HANDLER
from handler.event_handler import EVENT_HANDLER
from handler.scheduled_msg_handler import SCHEDULED_HANDLER
from LineHelper import LineHelper


app = Flask(__name__)

configuration = Configuration(
    access_token=os.getenv('CHANNEL_ACCESS_TOKEN', None))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET', None))

# init funcs
my_func.init_bluearchive_chars_data()


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
        app.logger.info(
            "Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


with ApiClient(configuration) as api_client:
    line_bot_api = MessagingApi(api_client)
scheduled_msg_handler = SCHEDULED_HANDLER(
    configuration=configuration, line_bot_api=line_bot_api)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    line_helper = LineHelper(line_bot_api, event)
    cmd_handler = CMD_HANDLER(
        event=event, line_bot_api=line_bot_api, line_helper=line_helper)
    event_handler = EVENT_HANDLER(
        event=event, line_bot_api=line_bot_api, line_helper=line_helper,)
    msg_handler = MSG_HANDLER(event=event, configuration=configuration,
                              line_bot_api=line_bot_api, cmd_handler=cmd_handler, event_handler=event_handler)
    msg_handler.handle()


if __name__ == "__main__":
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit) as e:
        # scheduler.shutdown()
        print(e)
