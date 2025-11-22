from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.shortcuts import render


# ---------------- HOME PAGE ----------------
def home(request):
    return render(request, "weather.html")

@api_view(['GET'])
def test(request):
    return Response({"message": "Weather API working"})

# ----------------- WEATHER CODES -----------------
WMO_CODES = {
    0: "Clear", 1: "Clear", 2: "Clouds", 3: "Clouds",
    45: "Fog", 48: "Fog",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle",
    56: "Drizzle", 57: "Drizzle",
    61: "Rain", 63: "Rain", 65: "Rain",
    66: "Rain", 67: "Rain",
    71: "Snow", 73: "Snow", 75: "Snow",
    77: "Snow",
    80: "Rain", 81: "Rain", 82: "Rain",
    85: "Snow", 86: "Snow",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
}

@api_view(['GET'])
def current_weather(request):
    city = request.GET.get('city', '').strip()

    if not city:
        return Response({"error": "City name is required"}, status=400)

    # 1) Geocoding
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_res = requests.get(geo_url).json()
    if "results" not in geo_res:
        return Response({"error": "City not found"}, status=404)

    place = geo_res["results"][0]
    lat, lon = place["latitude"], place["longitude"]
    
    # 2) Units
    unit = request.GET.get("unit", "celsius").lower()
    unit_param = "fahrenheit" if unit == "fahrenheit" else "celsius"

    # 3) Weather API Call
    forecast_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,visibility,wind_speed_10m"
        f"&hourly=temperature_2m,weather_code"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max,apparent_temperature_max,apparent_temperature_min,wind_speed_10m_max"
        f"&timezone=auto&temperature_unit={unit_param}"
    )
    weather_data = requests.get(forecast_url).json()

    # 4) Air Quality API Call
    aqi_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        f"&current=european_aqi"
    )
    aqi_data = requests.get(aqi_url).json()
    
    # 5) Process Current Weather
    current = weather_data["current"]
    current_weather = {
        "temp": round(current["temperature_2m"]),
        "description": WMO_CODES.get(current["weather_code"], "Clear"),
        "main": WMO_CODES.get(current["weather_code"], "Clear"),
    }

    # 6) Process Details
    details = {
        "feels_like": round(current["apparent_temperature"]),
        "wind_speed": round(current["wind_speed_10m"]),
        "humidity": current["relative_humidity_2m"],
        "visibility": round(current["visibility"] / 1000), # Meters to KM
        "uv_index": weather_data["daily"]["uv_index_max"][0],
        "aqi": aqi_data.get("current", {}).get("european_aqi", "n/a")
    }
    
    # 7) Process Hourly Forecast (next 12 hours)
    hourly = weather_data["hourly"]
    hourly_forecast = []
    for i in range(12):
        hourly_forecast.append({
            "time": hourly["time"][i][-5:], # "HH:MM"
            "temp": round(hourly["temperature_2m"][i]),
            "main": WMO_CODES.get(hourly["weather_code"][i], "Clear")
        })

    # 8) Process Daily Forecast (next 7 days)
    daily = weather_data["daily"]
    daily_forecast = []
    for i in range(7):
        daily_forecast.append({
            "day": daily["time"][i],
            "max_temp": round(daily["temperature_2m_max"][i]),
            "min_temp": round(daily["temperature_2m_min"][i]),
            "description": WMO_CODES.get(daily["weather_code"][i], "Clear"),
            "main": WMO_CODES.get(daily["weather_code"][i], "Clear"),
            "apparent_max": round(daily["apparent_temperature_max"][i]),
            "apparent_min": round(daily["apparent_temperature_min"][i]),
            "wind_speed": round(daily["wind_speed_10m_max"][i]),
            "uv_index": daily["uv_index_max"][i]
        })

    return Response({
        "city": place.get("name"),
        "country": place.get("country_code"),
        "current": current_weather,
        "details": details,
        "hourly": hourly_forecast,
        "daily": daily_forecast,
        "alerts": [] # Placeholder
    })
