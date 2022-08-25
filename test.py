
from django.conf import settings
import django
import logging
import pygsheets
import json
import re
from datetime import datetime
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LineBotServer.settings')

django.setup()


fileName = os.path.join(
    settings.BASE_DIR, 'docs/firstfirebase-f6e15-dcc94b5fa7ed.json')

emoji_product = "5ac21a8c040ab15980c9b43f"
emoji_start = 53
command = ["彩蛋", "指令", "週次", "變更", "跳過"]
command_list = [
    {
        "command": "指令:",
        "description": "輸入『指令』可以顯示機器人可以接受的指令"
    },
    {
        "command": "週次:",
        "description": "輸入『週次』可以顯示該週夜訓的主題為何"
    },
    {
        "command": "變更:",
        "description": "輸入『變更』可以將該週的主題做變換，ex:增員>業績 or 業績>增員"
    },
    {
        "command": "跳過:",
        "description": "輸入『跳過』可以將該週主題保留至下週，若下週為同心週，則繼續遞延"
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
        # print(idx, obj['command'], obj['description'])
        result += "${}{}\n".format(obj['command'], obj['description']) if len(command_list) - \
            idx != 1 else "${}{}".format(obj['command'], obj['description'])
    return result


def get_commands_emojis():
    result = []
    splitarr = get_commands().split("$")
    index = 0
    for idx, split_str in enumerate(splitarr):
        result.append(get_emoji("{:0>3d}".format(emoji_start+idx), index))
        index += (len(split_str)+2)
    return result


def get_employee_index_from_arr(employee, arr):
    index = -1
    for idx, str_value in enumerate(arr):
        if employee in str_value:
            index = idx
    return index


def get_update_result(input_text: str, row: list):

    ori_value = row[2]
    employee = row[1]
    level = None
    history_records = json.loads(row[3])
    if "reset" in input_text or "Reset" in input_text:
        return {
            "level": "三",
            "employee": employee,
            "updateValue": 254,
            "historyRecords": '{"history":[]}'
        }
    else:
        update_value = 0
        history = None
        modify_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "+" in input_text:
            update_value = float(ori_value) - float(input_text[5:-1])
            history = {
                "editTime": modify_time,
                "current": update_value,
                "input": float(input_text[5:-1]),
                "type": "Plus"
            }
        elif "-" in input_text:
            update_value = float(ori_value) + float(input_text[5:-1])
            history = {
                "editTime": modify_time,
                "current": update_value,
                "input": float(input_text[5:-1]),
                "type": "Minus"
            }
        else:
            update_value = float(input_text[4:-1])
            history = {
                "editTime": modify_time,
                "current": update_value,
                "input": float(input_text[4:-1]),
                "type": "Set"
            }

        update_value = 254 if update_value > 254 else update_value
        update_value = 0 if update_value < 0 else update_value

        history_records["history"].append(history)

        if update_value >= 200:
            level = "三"
        elif update_value >= 100:
            level = "二"
        else:
            level = "一"

        return {
            "level": level,
            "employee": employee,
            "updateValue": update_value,
            "historyRecords": json.dumps(history_records)
        }


def modify_performance(employee: str, input_text: str):
    gc = pygsheets.authorize(
        service_account_file=fileName)
    web_url = settings.GOOGLE_SHEET_URL
    wb_url = gc.open_by_url(web_url)
    sh = wb_url.worksheet("title", "MDRT")

    row_index = get_employee_index_from_arr(employee, sh.get_col(2))
    if row_index > -1:

        data = get_update_result(input_text, sh.get_row(row_index+1))

        sh.update_values('A{0}:D{0}'.format(row_index+1), [
            [data["level"], data["employee"], data["updateValue"], data["historyRecords"]]])

        return "Dear.{} 已將您的MDRT紀錄刷新為{:3.2f}p，目前為階段{}，再接再厲！".format(employee, data["updateValue"], data["level"])


def test_func():
    # total_command = get_commands()
    # splitcommand = total_command.split("$")
    # print(total_command)
    # print(splitcommand)
    target_string = "MDRT reset"
    try:
        command.index(target_string)
    except ValueError as e:
        regex_normal = re.compile(
            r"^MDRT[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?p")
        regex_reset = re.compile(r"^MDRT\s(Reset|reset)")
        normal_result = regex_normal.search(target_string)
        reset_result = regex_reset.search(target_string)
        if normal_result is None and reset_result is None:
            print("nothing match!{}".format(str(e)[::-1][15:][::-1]))
            logging.error('command: {} 不存在於系統中'.format(
                str(e)[::-1][15:][::-1]))
        message = modify_performance("測試", "MDRT+2.32p")
        print(message)
    # arr = ["a", "b", "c", "測試"]
    # print(any("測試 hahahahahha" in str_val for str_val in arr))
    # print("業績+2.32p"[3:-1], 32.23, float("32.23"))


test_func()
