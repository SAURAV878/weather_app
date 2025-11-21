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
    cities = {
        "pokhara" : (28.2096, 83.9856),
        "kathmandu" : (27.7, 85.32),
        "biratnagar": (26.48, 87.27)
    }
    
    city = request.GET.get ('city', 'pokhara').strip().lower()

    if city not in cities:
        return Response({
            "error":"City is not found"
        }, status=400)
    
    lat, lon = cities[city]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=GMT"


    response = requests.get(url)

    data = response.json()

    weather = data.get('current_weather', {})
    weather['latitude'] = data.get("latitude")
    weather['longitude'] = data.get("longitude")
    weather['elevation'] = data.get("elevation")
    weather['timezone'] = data.get("timezone")

   

    daily = data.get('daily', {})
    dates = daily.get('time', [])
    max_temps = daily.get('temperature_2m_max', [])
    min_temps = daily.get('temperature_2m_min', [])
    codes = daily.get('weathercode', [])

    forecast_list = []
    for i in range(len(dates)):
        forecast_list.append({
            'date': dates[i],
            'max': max_temps[i],
            'min': min_temps[i],
            'weathercode': codes[i]
        })



    return Response({
        'city': city.capitalize(),
        'current': weather,
        'forecast': forecast_list
    })



 
  














  