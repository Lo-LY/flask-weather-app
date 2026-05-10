from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Open-Meteo API endpoints
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_coordinates(city):
    """
    Convert city name to latitude and longitude using Open-Meteo Geocoding API.
    Returns tuple (lat, lon) or None if city not found.
    """
    try:
        params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        response = requests.get(GEOCODING_URL, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if "results" not in data or len(data["results"]) == 0:
            return None
        
        result = data["results"][0]
        return (result["latitude"], result["longitude"], result.get("name", city), result.get("country", ""))
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
        return None


def get_weather(lat, lon):
    """
    Fetch current weather data using latitude and longitude.
    Returns a dict with weather info or None on error.
    """
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit"
        }
        response = requests.get(WEATHER_URL, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        current = data.get("current", {})
        
        # Weather code to description mapping (simplified WMO codes)
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        weather_code = current.get("weather_code", 0)
        weather_description = weather_codes.get(weather_code, "Unknown")
        
        return {
            "temperature": round(current.get("temperature_2m", 0), 1),
            "feels_like": round(current.get("apparent_temperature", 0), 1),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_speed": round(current.get("wind_speed_10m", 0), 1),
            "condition": weather_description
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None


@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/weather", methods=["POST"])
def get_weather_for_city():
    """
    API endpoint to get weather for a given city.
    Expects JSON with 'city' field.
    """
    try:
        data = request.get_json()
        city = data.get("city", "").strip()
        
        if not city:
            return jsonify({"error": "Please enter a city name"}), 400
        
        # Get coordinates
        coords = get_coordinates(city)
        if not coords:
            return jsonify({"error": f"City '{city}' not found. Please try another city."}), 404
        
        lat, lon, city_name, country = coords
        
        # Get weather
        weather = get_weather(lat, lon)
        if not weather:
            return jsonify({"error": "Unable to fetch weather data. Please try again."}), 500
        
        weather["city"] = city_name
        weather["country"] = country
        return jsonify(weather), 200
        
    except Exception as e:
        print(f"Error in get_weather_for_city: {e}")
        return jsonify({"error": "An error occurred. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
