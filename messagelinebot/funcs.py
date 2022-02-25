from datetime import datetime, timedelta
import pygsheets
import os
import json
from django.conf import settings

fileName = os.path.join(
    settings.BASE_DIR, 'docs/firstfirebase-f6e15-dcc94b5fa7ed.json')
# 檢查當日是否為週二，且為當月最後一週


def check_is_last_tuesday():
    now = datetime.now()
    today_plus_7_day = now + timedelta(days=7)
    return now.isoweekday() == 2 and now.month != today_plus_7_day.month

# 調整夜訓的主題設定


def reverse_week_type(iscron=True):
    gc = pygsheets.authorize(
        service_account_file=fileName)
    web_url = settings.GOOGLE_SHEET_URL
    wb_url = gc.open_by_url(web_url)
    sh = wb_url.sheet1
    result_row = sh.get_row(2)
    # 如果是排程執行
    if iscron:
        # 如果該週不為最後一個週二
        if not check_is_last_tuesday():
            # 該週沒有跳過在執行
            if result_row[1] != "TRUE":
                result = result_row[0] == "TRUE"
                sh.cell("A2").value = not result
                return not result
            # 如果有跳過，就將pass 設定回 false
            else:
                sh.cell("B2").value = False
                return True
    else:
        result = result_row[0] == "TRUE"
        sh.cell("A2").value = not result
        return not result

# 跳過該週


def pass_this_week():
    gc = pygsheets.authorize(
        service_account_file=fileName)
    web_url = "https://docs.google.com/spreadsheets/d/1v0G4cp02Qq4zM7miulrqixL0tbR5v_yoASRdoTa5I9U"
    wb_url = gc.open_by_url(web_url)
    sh = wb_url.sheet1
    sh.cell("B2").value = True

# 判斷該週的主題內容是什麼


def get_week_type():
    gc = pygsheets.authorize(
        service_account_file=fileName)
    web_url = "https://docs.google.com/spreadsheets/d/1v0G4cp02Qq4zM7miulrqixL0tbR5v_yoASRdoTa5I9U"
    wb_url = gc.open_by_url(web_url)
    sh = wb_url.sheet1

    return sh.cell("A2").value == "TRUE"


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
    return "Dear.{} 你不在MDRT的挑戰參與者中，請連絡主管將你加入挑戰團隊！".format(employee)


def switch_training_subject():
    reverse_week_type(True)
