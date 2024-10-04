import appdaemon.plugins.hass.hassapi as hass

from datetime import datetime, timedelta
import weather_api as weather

ROOMS = ["conservatory", "dining_room", "lounge", "office", "bedroom", "pink_room"]
OUTSIDE_TEMP = 12
INSIDE_TEMP = 17

class TadoHeatControl(hass.Hass):

    def initialize(self):
        self.log("*************************************************************************")
        self.log("TadoHeatControl initialized")
        self.log("*************************************************************************")
        now = datetime.now().replace(second=5, microsecond=0)
        start_time = now + timedelta(minutes=15 - now.minute % 15)
        self.run_at(self.main, datetime.now() + timedelta(seconds=5))
        self.run_every(self.main, start_time, interval=60 * 15)

    def main(self, kwargs):
        self.log("*************************************************************************")
        self.log("Starting update cycle")
        self.log(f"Inside temperature set to: {INSIDE_TEMP} C")
        self.log(f"Outside temperature set to: {OUTSIDE_TEMP} C")

        data = weather.get_weather_data(hass=self)
        weather.daily_entities(hass=self, data=data)
        weather.hourly_entities(hass=self, data=data)
        self.tado_control(data=data)

    def tado_control(self, data):
        heating_required = False

        temp_hour_0 = data["hourly"][0]["temp"]
        temp_hour_1 = data["hourly"][1]["temp"]
        temp_hour_2 = data["hourly"][2]["temp"]
        temps = [temp_hour_0, temp_hour_1, temp_hour_2]

        self.log(f"Temps: Hour 0: {temp_hour_0}, Hour 1: {temp_hour_1}, Hour 2: {temp_hour_2}")

        for temp in temps:
            if temp >= OUTSIDE_TEMP:
                heating_required = False
                break
            else:
                heating_required = True

        for room in ROOMS:
            room_temperature = self.get_state(f"sensor.{room}_temperature")
            self.log(f"Temperature in {room}: {room_temperature}")

            room_climate = self.get_state(f"climate.{room}")
            self.log(f"Climate in {room}: {room_climate}")

            if room_climate == "off" and float(room_temperature) < INSIDE_TEMP:
                self.call_service(service="climate/set_hvac_mode", entity_id=f"climate.{room}", hvac_mode="auto")
                self.log(f"Room temperature less than {INSIDE_TEMP} C and climate set to {room_climate} so turning {room} to auto")

            elif room_climate == "off" and heating_required == True:
                self.call_service(service="climate/set_hvac_mode", entity_id=f"climate.{room}", hvac_mode="auto")
                self.log(f"Outside temperature will be below {OUTSIDE_TEMP} C in the next 3 hours so turning {room} to auto")

            elif room_climate == "auto" and heating_required == False and float(room_temperature) >= INSIDE_TEMP:
                self.call_service(service="climate/set_hvac_mode", entity_id=f"climate.{room}", hvac_mode="off")
                self.log(f"Outside temperature will be above {OUTSIDE_TEMP} in the next 3 hours so turning {room} to off")

            else:
                self.log(f"No change needed in {room}")

        self.log("Update cycle finished")
        self.log("*************************************************************************")
