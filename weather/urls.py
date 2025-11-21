from django.urls import path
from .views import test, current_weather,home

urlpatterns = [
    path('test/', test),
    path('current_weather/', current_weather),
    path('home/',home),
]