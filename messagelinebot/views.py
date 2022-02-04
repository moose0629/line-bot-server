import json
import calendar
import logging
from . import funcs
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

emoji_product = "5ac21a8c040ab15980c9b43f"
emoji_num1 = "053"
emoji_num2 = "054"
emoji_num3 = "055"


def get_emoji(emoji_num: str, index: int):
    return {
        "index": index,
        "productId": emoji_product,
        "emojiId": emoji_num
    }


def handle_message_text(message_text: str):
    if message_text == "指令":
        return TextSendMessage(
            text="$指令\n$週次\n$績效",
            emojis=[
                get_emoji(emoji_num1, 0),
                get_emoji(emoji_num2, 4),
                get_emoji(emoji_num3, 8)
            ]
        )
    elif message_text == "週次":
        if funcs.check_is_last_tuesday():
            return TextSendMessage("這週夜訓是『向心週』")
        elif funcs.get_week_type():
            return TextSendMessage("這週夜訓是『徵員週』")
        else:
            return TextSendMessage("這週夜訓是『激勵週』")
    elif message_text == "跳過":
        funcs.pass_this_week()
        return TextSendMessage("已跳過這週夜訓")
    elif message_text == "變更":
        result = funcs.reverse_week_type(False)
        return TextSendMessage("已將這週夜訓變更為『{}』".format("徵員週" if result else "激勵週"))
    else:
        return TextSendMessage(message_text)


@csrf_exempt
def callback(request):
    # print(json.dumps(request))
    print("hello line bot connected")

    try:
        if request.method == 'POST':
            signature = request.META['HTTP_X_LINE_SIGNATURE']
            body = request.body.decode('utf-8')

            try:
                events = parser.parse(body, signature)  # 傳入的事件
            except InvalidSignatureError:
                return HttpResponseForbidden()
            except LineBotApiError:
                return HttpResponseBadRequest()

            for event in events:
                if isinstance(event, MessageEvent) and event.message.type == 'text':  # 如果有訊息事件
                    user_key_in = event.message.text

                    line_bot_api.reply_message(  # 回復傳入的訊息文字
                        event.reply_token,
                        handle_message_text(user_key_in)
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage("請輸入文字")
                    )
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    except Exception as e:  # work on python 3.x
        logging.error('Failed to upload to ftp: ' + str(e))


@csrf_exempt
def test(request):
    print("test!!!")
    return HttpResponse("success")
