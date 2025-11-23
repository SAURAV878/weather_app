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


# ----------------- WEATHER CODES (Exact) -----------------
WMO_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Freezing Drizzle",
    57: "Freezing Heavy Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Freezing Rain",
    67: "Freezing Heavy Rain",
    71: "Slight Snowfall",
    73: "Moderate Snowfall",
    75: "Heavy Snowfall",
    77: "Snow Grains",
    80: "Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm With Hail",
    99: "Severe Thunderstorm With Hail"
}


# ----------------- MAIN WEATHER API -----------------
@api_view(['GET'])
def current_weather(request):
    city = request.GET.get('city', '').strip()

    if not city:
        return Response({"error": "City name is required"}, status=400)

    # 1) Geocoding
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_res = requests.get(geo_url).json()

    # FIX: Prevent wrong weather for non-existing city
    if not geo_res.get("results"):
        return Response({"error": "City not found or invalid input"}, status=404)

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
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max,apparent_temperature_max,apparent_temperature_min,wind_speed_10m_max,precipitation_probability_max"
        f"&timezone=auto&temperature_unit={unit_param}&forecast_days=7"
    )
    weather_data = requests.get(forecast_url).json()

    # 4) Air Quality API
    aqi_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        f"&current=european_aqi"
    )
    aqi_data = requests.get(aqi_url).json()

    # 5) CURRENT WEATHER
    current = weather_data["current"]
    current_weather = {
        "temp": round(current["temperature_2m"]),
        "main": WMO_CODES.get(current["weather_code"], "Clear Sky"),
        "description": WMO_CODES.get(current["weather_code"], "Clear Sky"),
    }

    # 6) CURRENT DETAILS
    details = {
        "feels_like": round(current["apparent_temperature"]),
        "wind_speed": round(current["wind_speed_10m"]),
        "humidity": current["relative_humidity_2m"],
        "visibility": round(current["visibility"] / 1000),  # meters → km
        "uv_index": weather_data["daily"]["uv_index_max"][0],
        "aqi": aqi_data.get("current", {}).get("european_aqi", "N/A")
    }

    # 7) HOURLY FORECAST (now for all 7 days)
    hourly = weather_data["hourly"]
    hourly_forecast = []
    for i in range(len(hourly["time"])):
        hourly_forecast.append({
            "time": hourly["time"][i], # Full ISO timestamp
            "temp": round(hourly["temperature_2m"][i]),
            "main": WMO_CODES.get(hourly["weather_code"][i], "Clear Sky")
        })


    # 8) DAILY FORECAST (next 7 days)
    daily = weather_data["daily"]
    daily_forecast = []
    for i in range(7):
        daily_forecast.append({
            "day": daily["time"][i],
            "max_temp": round(daily["temperature_2m_max"][i]),
            "min_temp": round(daily["temperature_2m_min"][i]),
            "description": WMO_CODES.get(daily["weather_code"][i], "Clear Sky"),
            "main": WMO_CODES.get(daily["weather_code"][i], "Clear Sky"),
            "apparent_max": round(daily["apparent_temperature_max"][i]),
            "apparent_min": round(daily["apparent_temperature_min"][i]),
            "wind_speed": round(daily["wind_speed_10m_max"][i]),
            "uv_index": daily["uv_index_max"][i],
            "precipitation_probability": daily["precipitation_probability_max"][i]
        })

    # RESPONSE
    return Response({
        "city": place.get("name"),
        "country": place.get("country"),
        "latitude": lat,
        "longitude": lon,
        "current": current_weather,
        "details": details,
        "hourly": hourly_forecast,
        "daily": daily_forecast,
        "alerts": []
    })
