#Standard
import requests
import time
import sys
import config

#Third Party
from datetime import datetime, date

class NextTrain():
    def __init__(self):
        self.number = 0

    def determineNext(self):
        # Setting the parameters to access the MBTA API data
        URL = 'https://api-v3.mbta.com/schedules'
        # Forest Hills
        stop = 70001
        route = 'Orange'
        direction_id = 1
        sort = 'departure_time'
        limit = 1


        now = datetime.now()
        date = now.date()
        # API requires HH:MM
        min_time = f"{now.hour}:{now.minute}"

        PARAMS = {'stop':stop,
                  'route':route,
                  'direction_id':direction_id,
                  'min_time':min_time,
                  'date':date,
                  'sort':sort}

        r = requests.get(URL, params = PARAMS)

        # If you get anything other than a good request, flag and exit
        if r.status_code != requests.codes.ok:
            print("Error: Bad Request")
            sys.exit()

        data = r.json()

        # I want to find a better way to access the info. To-do
        next = data['data'][0]['attributes']['departure_time']

        # If MBTA changes how their data is stored, this should be flagged here
        if not next:
            print("MBTA JSON format has changed: adjust appropriately")
            sys.exit()

        # Sending along the necessary info to the next stage
        return [next, date, now]

    def determineTemp(self):
        key = config.api_key
        city_id = 4930956

        URL = "http://api.openweathermap.org/data/2.5/weather"
        PARAMS = {'appid':key,
                  'id':city_id}

        r = requests.get(URL, PARAMS)

        if r.status_code != requests.codes.ok:
            print("Error: Bad Request")
            sys.exit()

        data = r.json()

        conditions = data['weather'][0]['main']
        conditionsDescriptive = data['weather'][0]['description']
        currentTemp = int((float(data['main']['temp']) - 273.15) * 9/5 + 32)

        return [conditions, conditionsDescriptive, currentTemp]

    def run(self):
        next = self.determineNext()[0]
        today = self.determineNext()[1]
        time = self.determineNext()[2].replace(microsecond=0) #drop microsecond
        weather = self.determineTemp()

        # Converting the string from JSON into datetime type
        nextDate = datetime.strptime(next.split("T")[0], '%Y-%m-%d').date()
        nextTime = datetime.strptime(next.split("T")[1].split("-")[0], '%H:%M:%S').time()

        next = datetime.combine(nextDate, nextTime)

        difference = next - time
        if difference.days < 0:
            print("Wait for MBTA data to update")
            sys.exit()
        else:
            print(f"Next Train at: {next.time()}({difference} left)")
            print(f"Current Weather: {weather[2]}F and {weather[0]} ({weather[1]})")

        # Add Database Code Below

# Main Function
if __name__ == "__main__":
    temp = NextTrain()
    temp.run()
