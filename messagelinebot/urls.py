from django.urls import path
from . import views

# 此處註冊路由, 所有路徑都可以在這裡解析判斷
urlpatterns = [
    path('callback', views.callback),
    path('test', views.test)
]
