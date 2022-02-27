import re
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
commands = ["指令", "週次", "變更", "跳過", "MDRT"]
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
    {
        "command": "MDRT：",
        "description": "\n輸入 『MDRT』 可以查閱MDRT紀錄的相關指令"
    }
]

mdrt_command_list = [
    {
        "command": "MDRT +xxxp",
        "description": "\n輸入 『MDRT+xxxp』 可以將MDRT的紀錄刷新。ex: MDRT+2.31p；結果 254p -> 251.69p"
    },
    {
        "command": "MDRT -xxxp",
        "description": "\n輸入 『MDRT-xxxp』 可以將MDRT的紀錄刷新。ex: MDRT-2.31p；結果 251.69p -> 254p"
    },
    {
        "command": "MDRT xxxp",
        "description": "\n輸入 『MDRT xxxp』 可以將MDRT的紀錄直接更新為該數值。ex: MDRT 2.31p；結果 251.69p -> 2.31p"
    },
    {
        "command": "MDRT reset",
        "description": "\n輸入 『MDRT reset』 可以將MDRT的紀錄重設。ex: MDRT reset；結果 251.69p -> 254p"
    },
    {
        "command": "MDRT search",
        "description": "\n輸入 『MDRT search』 可以查詢自己目前的MDRT紀錄。ex: MDRT search"
    }
]

regex_normal = re.compile(
    r"^MDRT\s*[+-]?(\d+(\.\d*)?|\.\d+)[pP]")
regex_search = re.compile(r"^MDRT\s(查詢|Search|search)")
regex_reset = re.compile(r"^MDRT\s(Reset|reset)")


def get_emoji(emoji_num: str, index: int):
    return {
        "index": index,
        "productId": emoji_product,
        "emojiId": emoji_num
    }


def get_commands():
    result = ""
    for idx, obj in enumerate(command_list):
        result += "${}{}\n".format(obj['command'], obj['description']) if len(command_list) - \
            idx != 1 else "${}{}".format(obj['command'], obj['description'])
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


def get_mdrt_instructions():
    result = ""
    for idx, obj in enumerate(mdrt_command_list):
        result += "${}{}\n".format(obj['command'], obj['description']) if len(mdrt_command_list) - \
            idx != 1 else "${}{}".format(obj['command'], obj['description'])
    return result


def get_mdrt_instructions_emojis():
    result = []
    splitarr = get_mdrt_instructions().split("$")
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
    elif message_text == "MDRT":
        return TextSendMessage(text=get_mdrt_instructions(), emojis=get_mdrt_instructions_emojis())
    else:
        return TextSendMessage("沒有這種東西 ヽ(́◕◞౪◟◕‵)ﾉ")


def handle_message_event(event):
    if isinstance(event, MessageEvent) and event.message.type == 'text':  # 如果有訊息事件
        user_key_in: str = event.message.text
        profile = line_bot_api.get_profile(event.source.user_id)
        user_key_in = user_key_in.strip()
        try:
            (["彩蛋"] + commands).index(user_key_in)

            line_bot_api.reply_message(  # 回復傳入的訊息文字
                event.reply_token,
                handle_message_text(user_key_in)
            )
            return HttpResponse()
        except ValueError as e:

            normal_result = regex_normal.search(user_key_in)
            search_result = regex_search.search(user_key_in)
            reset_result = regex_reset.search(user_key_in)
            if normal_result is None and reset_result is None and search_result is None:
                logging.error('command: {} 不存在於系統中'.format(
                    str(e)[::-1][15:][::-1]))
            elif search_result is not None:
                result = funcs.search_performance(profile.display_name)

                line_bot_api.reply_message(  # 回復傳入的訊息文字
                    event.reply_token,
                    TextSendMessage(result)
                )
            else:
                line_bot_api.reply_message(  # 回復傳入的訊息文字
                    event.reply_token,
                    TextSendMessage(funcs.modify_performance(
                        profile.display_name, user_key_in))
                )
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


@ csrf_exempt
def test(request):
    print("test!!!")
    return HttpResponse("success")
