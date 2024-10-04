import requests
from datetime import datetime, timedelta

BASE_URL = "https://api.openweathermap.org/data/3.0/onecall?"

def convert_time(unix_time):
    readable_time = datetime.fromtimestamp(unix_time)
    formatted_time = readable_time.strftime('%H:%M - %d %B %Y')
    return formatted_time

def convert_time_date_only(unix_time):
    readable_time = datetime.fromtimestamp(unix_time)
    formatted_time = readable_time.strftime('%d %B %Y')
    return formatted_time

def get_weather_data(hass):
    latitude = hass.args.get("latitude")
    longitude = hass.args.get("longitude")
    api = hass.args.get("open_weather_api")

    fullUrl = f"{BASE_URL}lat={latitude}&lon={longitude}&appid={api}&units=metric"
    data = requests.get(fullUrl)
    status = data.status_code
    hass.log(f"Get weather data fullUrl: {fullUrl}")
    hass.log(f"Status code: {status}")
    return data.json()


def daily_entities(hass, data):
    daily_data = data["daily"]
    for day in range(0, 8):
        rain = daily_data[day].get("rain", "No Data")
        if rain == "No Data":
            hass.log(f"No Rain data found for {convert_time_date_only(daily_data[day]['dt'])} using default message", level="DEBUG")

        # TODO Need to add snow data

        try:
            hass.set_state(f"sensor.open_weather_day_{day}", state=daily_data[day]["temp"]["day"], attributes={
                "friendly_name": convert_time_date_only(daily_data[day]["dt"]),
                "unit_of_measurement": "°C",
                "Sunrise": convert_time(daily_data[day]["sunrise"]),
                "Sunset": convert_time(daily_data[day]["sunset"]),
                "Moonrise": convert_time(daily_data[day]["moonrise"]),
                "Moonset": convert_time(daily_data[day]["moonset"]),
                "Moon phase": daily_data[day]["moon_phase"],
                "Summary": daily_data[day]["summary"],
                "Temp - Day": daily_data[day]["temp"]["day"],
                "Temp - Min": daily_data[day]["temp"]["min"],
                "Temp - Max": daily_data[day]["temp"]["max"],
                "Temp - Night": daily_data[day]["temp"]["night"],
                "Temp - Eve": daily_data[day]["temp"]["eve"],
                "Temp - Morn": daily_data[day]["temp"]["morn"],
                "Feels like - Day": daily_data[day]["feels_like"]["day"],
                "Feels like - Night": daily_data[day]["feels_like"]["night"],
                "Feels like - Eve": daily_data[day]["feels_like"]["eve"],
                "Feels like - Morn": daily_data[day]["feels_like"]["morn"],
                "Pressure": daily_data[day]["pressure"],
                "Humidity": daily_data[day]["humidity"],
                "Dew point": daily_data[day]["dew_point"],
                "Wind speed": daily_data[day]["wind_speed"],
                "Wind degrees": daily_data[day]["wind_deg"],
                "Wind gust": daily_data[day]["wind_gust"],
                "Weather - ID": daily_data[day]["weather"][0]["id"],
                "Weather - Main": daily_data[day]["weather"][0]["main"],
                "Weather - Description": daily_data[day]["weather"][0]["description"],
                "Clouds": daily_data[day]["clouds"],
                "POP": daily_data[day]["pop"],
                "Rain": rain,
                "UVI": daily_data[day]["uvi"],
            })
        except KeyError as e:
            missing_key = str(e).strip("'")
            hass.log(f"KeyError: Missing key '{missing_key}' in daily data for "
                     f"{convert_time_date_only(daily_data[day]['dt'])}", level="ERROR")
            hass.set_state(f"sensor.open_weather_day_{day}", state=daily_data[day]["temp"]["day"], attributes={
                "friendly_name": f"{convert_time_date_only(daily_data[day]['dt'])} E",
                "unit_of_measurement": "°C",
            })

    hass.log("Daily entities created / updated")

def hourly_entities(hass, data):
    hourly_data = data["hourly"]
    for hour in range(0, 12):
        wind_gust = hourly_data[hour].get("wind_gust", "No Data")
        if wind_gust == "No Data":
            hass.log(f"No Wind Gust data found for {convert_time(hourly_data[hour]['dt'])} using default message", level="DEBUG")

        rain = hourly_data[hour].get("rain", "No Data")  # TODO Need to check when it rains if this is formated correctly
        if rain == "No Data":
            hass.log(f"No Rain data found for {convert_time(hourly_data[hour]['dt'])} using default message", level="DEBUG")

        snow = hourly_data[hour].get("snow", "No Data")  # TODO format the same as rain
        if snow == "No Data":
            hass.log(f"No Snow data found for {convert_time(hourly_data[hour]['dt'])} using default message", level="DEBUG")

        try:
            hass.set_state(f"sensor.open_weather_hour_{hour}", state=hourly_data[hour]["temp"], attributes={
                "friendly_name": convert_time(hourly_data[hour]["dt"]),
                "unit_of_measurement": "°C",
                "Feels like": hourly_data[hour]["feels_like"],
                "Pressure": hourly_data[hour]["pressure"],
                "Humidity": hourly_data[hour]["humidity"],
                "Dew point": hourly_data[hour]["dew_point"],
                "UVI": hourly_data[hour]["uvi"],
                "Clouds": hourly_data[hour]["clouds"],
                "Visibility": hourly_data[hour]["visibility"],
                "Wind speed": hourly_data[hour]["wind_speed"],
                "Wind gust": wind_gust,
                "Wind degrees": hourly_data[hour]["wind_deg"],
                "POP": hourly_data[hour]["pop"],
                "Rain - 1h": rain,
                "Snow - 1h": snow,
                "Weather - ID": hourly_data[hour]["weather"][0]["id"],
                "Weather - Main": hourly_data[hour]["weather"][0]["main"],
                "Weather - Description": hourly_data[hour]["weather"][0]["description"],
            })

        except KeyError as e:
            missing_key = str(e).strip("'")
            hass.log(f"KeyError: Missing key '{missing_key}' in hourly data for "
                     f"{convert_time(hourly_data[hour]['dt'])}", level="ERROR")
            hass.set_state(f"sensor.open_weather_hour_{hour}", state=hourly_data[hour]["temp"], attributes={
                "friendly_name": f"{convert_time(hourly_data[hour]['dt'])} E",
                "unit_of_measurement": "°C",
            })

    hass.log("Hourly entities created / updated")

