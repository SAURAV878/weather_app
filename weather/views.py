from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests


@api_view(['GET'])
def current_weather(request):
    city = request.GET.get('city', '').strip()

    if not city:
        return Response({"error": "City name is required"}, status=400)

    # ------------------------------------------
    # 1) GEOCODING API – Convert City → Lat/Lon
    # ------------------------------------------
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_res = requests.get(geo_url).json()

    if "results" not in geo_res:
        return Response({"error": "City not found"}, status=404)

    place = geo_res["results"][0]

    city_name = place["name"]
    country = place["country"]
    lat = place["latitude"]
    lon = place["longitude"]

    # ------------------------------------------
    # 2) UNIT SELECTION
    # ------------------------------------------
    unit = request.GET.get("unit", "celsius").lower()
    unit_param = "fahrenheit" if unit == "fahrenheit" else "celsius"

    # ------------------------------------------
    # 3) NUMBER OF FORECAST DAYS
    # ------------------------------------------
    days = int(request.GET.get("days", 7))

    # ------------------------------------------
    # 4) MAIN WEATHER API
    # ------------------------------------------
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current_weather=true&"
        f"daily=temperature_2m_max,temperature_2m_min,weathercode&"
        f"timezone=GMT&temperature_unit={unit_param}&forecast_days={days}"
    )

    data = requests.get(url).json()

    # ------------------------------------------
    # 5) WEATHER CODE → HUMAN DESCRIPTION
    # ------------------------------------------
    weather_codes = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Fog 🌫",
        48: "Depositing rime fog 🌫",
        51: "Light drizzle 🌦",
        53: "Moderate drizzle 🌦",
        55: "Dense drizzle 🌧",
        61: "Light rain 🌧",
        63: "Moderate rain 🌧",
        65: "Heavy rain 🌧",
        71: "Light snow ❄️",
        73: "Moderate snow ❄️",
        75: "Heavy snow ❄️",
        80: "Rain showers 🌦",
        81: "Moderate rain showers 🌧",
        82: "Violent rain showers 🌧",
    }

    # ------------------------------------------
    # 6) CURRENT WEATHER EXTRA DATA
    # ------------------------------------------
    current = data.get("current_weather", {})
    current_code = current.get("weathercode", 0)
    current["weather_description"] = weather_codes.get(current_code, "Unknown")

    # ------------------------------------------
    # 7) FORECAST FOR NEXT DAYS
    # ------------------------------------------
    daily = data.get("daily", {})
    forecast_list = []

    for i in range(len(daily.get("time", []))):
        code = daily.get("weathercode", [])[i]
        forecast_list.append({
            "date": daily["time"][i],
            "max": daily["temperature_2m_max"][i],
            "min": daily["temperature_2m_min"][i],
            "weathercode": code,
            "description": weather_codes.get(code, "Unknown"),
        })

    # ------------------------------------------
    # 8) SEND FINAL JSON RESPONSE
    # ------------------------------------------
    return Response({
        "city": city_name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "unit": unit_param,
        "current": current,
        "forecast": forecast_list
    })
