from datetime import datetime, timedelta
import pygsheets
import os
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


def switch_training_subject():
    reverse_week_type(True)
