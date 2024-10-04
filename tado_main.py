import appdaemon.plugins.hass.hassapi as hass

from datetime import datetime, timedelta
import weather_api as weather

ROOMS = {
    "conservatory": {"morning": 17, "day": 18, "sun_correction": 2},
    "dining_room": {"morning": 17, "day": 18, "sun_correction": 2},
    "lounge": {"morning": 17, "day": 18, "sun_correction": 0},
    "office": {"morning": 17, "day": 17, "sun_correction": 0},
    "bedroom": {"morning": 17, "day": 17, "sun_correction": 0},
    "pink_room": {"morning": 17, "day": 17, "sun_correction": 0},
}

OUTSIDE_TEMP = 12
MORNING_ENDS = (15, 0)

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
        self.log("*************************************************************************")
        self.log(f"Outside temperature set to: {OUTSIDE_TEMP} C")
        
        # Get data from weather api
        data = weather.get_weather_data(hass=self)

        sunrise = datetime.fromtimestamp(data["current"]["sunrise"]).time()
        current_weather_id = data["current"]["weather"][0]["id"]
        current_weather_condition = data["current"]["weather"][0]["description"]
        
        # Update weather entities
        weather.hourly_entities(hass=self, data=data)
        weather.daily_entities(hass=self, data=data)

        # Finds temperatures next 3 hours
        temp_hour_0 = data["hourly"][0]["temp"]
        temp_hour_1 = data["hourly"][1]["temp"]
        temp_hour_2 = data["hourly"][2]["temp"]
        temps = [temp_hour_0, temp_hour_1, temp_hour_2]

        # Considers True or False if heating required based on outside temperature
        heating_required = False
        for temp in temps:
            if temp >= OUTSIDE_TEMP:
                heating_required = False
                break
            else:
                heating_required = True

        self.log("*************************************************************************")

        # Iterate through rooms and apply settings
        for room_name, room_data in ROOMS.items():
            self.log(room_name.upper().replace('_', ' '))

            # Obtain Tado data
            room_temperature = self.get_state(f"sensor.{room_name}_temperature")
            room_climate = self.get_state(f"climate.{room_name}")

            # Log entries
            self.log(f"Room Temperature: {room_temperature}")
            self.log(f"Climate Setting: {room_climate}")
            self.log(f"Temps: Hour 0: {temp_hour_0}, Hour 1: {temp_hour_1}, Hour 2: {temp_hour_2}")
            self.log(f"Heating required: {heating_required}")
            self.log(f"Sunrise time: {sunrise}")
            self.log(f"Current weather - ID: {current_weather_id}, Condition: {current_weather_condition}")

            # Set minimum room temperature based on time and room
            if sunrise <= datetime.now().time() < datetime.now().time().replace(hour=MORNING_ENDS[0], minute=MORNING_ENDS[1]):
                room_minimum_temp = room_data["morning"]
                self.log(f"Morning: Minimum room temperature: {room_minimum_temp} C")

                # Adjusts room temperature based on sunshine
                if 800 <= current_weather_id <= 802:
                    room_minimum_temp = room_minimum_temp - room_data["sun_correction"]
                    self.log(f"Sun Correction: {room_data['sun_correction']} C")
                    self.log(f"Minimum room temperature after sun correction: {room_minimum_temp} C")
            else:
                room_minimum_temp = room_data["day"]
                self.log(f"Afternoon / Evening: Minimum room temperature: {room_minimum_temp} C")

            # Main logical questions
            if room_climate == "off" and float(room_temperature) < room_minimum_temp:
                self.call_service(service="climate/set_hvac_mode", entity_id=f"climate.{room_name}", hvac_mode="auto")
                self.log(f"Room temperature less than {room_minimum_temp} C and climate set to {room_climate} so turning to auto")

            elif room_climate == "off" and heating_required == True:
                self.call_service(service="climate/set_hvac_mode", entity_id=f"climate.{room_name}", hvac_mode="auto")
                self.log(f"Outside temperature will be below {OUTSIDE_TEMP} C in the next 3 hours so turning to auto")

            elif room_climate == "auto" and heating_required == False and float(room_temperature) >= room_minimum_temp:
                self.call_service(service="climate/set_hvac_mode", entity_id=f"climate.{room_name}", hvac_mode="off")
                self.log(f"Outside temperature will be above {OUTSIDE_TEMP} in the next 3 hours so turning to off")

            else:
                self.log("No change needed")

            self.log("*************************************************************************")

        self.log("Update cycle finished")
        self.log("*************************************************************************")


