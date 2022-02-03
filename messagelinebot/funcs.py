import pygsheets
import json
import os

fileDir = os.path.dirname(os.path.realpath('__file__'))
fileName = os.path.join(fileDir, 'docs\\firstfirebase-f6e15-dcc94b5fa7ed.json')


def reverse_week_type():

    gc = pygsheets.authorize(
        service_account_file=fileName)
    web_url = "https://docs.google.com/spreadsheets/d/1v0G4cp02Qq4zM7miulrqixL0tbR5v_yoASRdoTa5I9U"
    wb_url = gc.open_by_url(web_url)
    sh = wb_url.sheet1

    result = json.loads(sh.cell("A1").value)
    result['is_recruit_week'] = not result['is_recruit_week']
    sh.cell("A1").value = json.dumps(result)


def get_week_type():
    gc = pygsheets.authorize(
        service_account_file=fileName)
    web_url = "https://docs.google.com/spreadsheets/d/1v0G4cp02Qq4zM7miulrqixL0tbR5v_yoASRdoTa5I9U"
    wb_url = gc.open_by_url(web_url)
    sh = wb_url.sheet1

    return json.loads(sh.cell("A1").value)['is_recruit_week']
