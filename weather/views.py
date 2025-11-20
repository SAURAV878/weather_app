from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests

@api_view(['GET'])
def test(request):
    return Response({
        'message': 'Weather Api working'
    })

# Create your views here.
@api_view(['GET'])
def current_weather(request):
    lat = request.GET.get('lat', '28.2096')
    lon = request.GET.get('lon', '83.9856')

    url =f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

    response = requests.get(url)

    data =  response.json()

    weather = data.get('current_weather', {})

    return Response(weather)