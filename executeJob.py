import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LineBotServer.settings')
import django

django.setup()
from messagelinebot.funcs import switch_training_subject


def run_job():
    print("run job!")
    switch_training_subject()

run_job()
