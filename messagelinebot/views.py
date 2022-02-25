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
emoji_start = 53
commands = ["指令", "週次", "變更", "跳過"]
command_list = [
    {
        "command": "指令：",
        "description": "\n輸入 『指令』 可以顯示機器人可以接受的指令及指令介紹。"        
    },
    {
        "command": "週次：",
        "description": "\n輸入 『週次』 可以顯示該週夜訓的主題。"
    },
    {
        "command": "變更：",
        "description": "\n輸入 『變更』 可以將該週的主題做變換。\nex：增員>業績 or 業績>增員"
    },
    {
        "command": "跳過：",
        "description": "\n輸入 『跳過』 可以將該週主題保留至下週，若下週為同心週，則繼續遞延。"
    },
]


def get_emoji(emoji_num: str, index: int):
    return {
        "index": index,
        "productId": emoji_product,
        "emojiId": emoji_num
    }


def get_commands():
    result = ""
    for idx, obj in enumerate(command_list):
        result += "${}{}\n".format(obj['command'],obj['description']) if len(command_list) - \
            idx != 1 else "${}{}".format(obj['command'],obj['description'])
    return result


def get_commands_emojis():
    result = []
    splitarr = get_commands().split("$")
    splitarr.pop(0)    
    index = 0
    for idx, split_str in enumerate(splitarr):
        result.append(get_emoji("{:0>3d}".format(emoji_start+idx), index))
        index += (len(split_str)+1)
    return result


def handle_message_text(message_text: str):
    if message_text == "指令":
        return TextSendMessage(
            text=get_commands(),
            emojis=get_commands_emojis()
        )
    elif message_text == "週次":
        if funcs.check_is_last_tuesday():
            return TextSendMessage("這週夜訓是『同心週』")
        elif funcs.get_week_type():
            return TextSendMessage("這週夜訓是『增員週』")
        else:
            return TextSendMessage("這週夜訓是『業績週』")
    elif message_text == "跳過":
        funcs.pass_this_week()
        return TextSendMessage("已跳過這週夜訓")
    elif message_text == "變更":
        result = funcs.reverse_week_type(False)
        return TextSendMessage("已將這週夜訓變更為『{}』".format("徵員週" if result else "業績週"))
    else:
        return TextSendMessage("沒有這種東西 ヽ(́◕◞౪◟◕‵)ﾉ")

def handle_message_event(event):
    if isinstance(event, MessageEvent) and event.message.type == 'text':  # 如果有訊息事件
        user_key_in = event.message.text

        try:
            (["彩蛋"] + commands).index(user_key_in)

            line_bot_api.reply_message(  # 回復傳入的訊息文字
                event.reply_token,
                handle_message_text(user_key_in)
            )
            return HttpResponse()
        except ValueError as e:
            logging.error('command: {} 不存在於系統中'.format(
                str(e)[::-1][15:][::-1]))
            return HttpResponse()


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
                handle_message_event(event)
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    except Exception as e:  # work on python 3.x
        logging.error('Failed to upload to ftp: ' + str(e))


@csrf_exempt
def test(request):
    print("test!!!")
    return HttpResponse("success")
