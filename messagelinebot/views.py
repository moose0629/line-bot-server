import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
def callback(request):
    # print(json.dumps(request))
    print("hello line bot connected")
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
            if isinstance(event, MessageEvent):  # 如果有訊息事件
                user_key_in = event.message.text

                if user_key_in == "指令":
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage("1.指令\n2.週次\n3.績效")
                    )
                else:
                    print(event.message.text)

                    line_bot_api.reply_message(  # 回復傳入的訊息文字
                        event.reply_token,
                        TextSendMessage(text=event.message.text)
                    )
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


@csrf_exempt
def test(request):
    print("test!!!")
    return HttpResponse("success")
