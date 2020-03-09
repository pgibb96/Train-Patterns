#Standard
import requests
import time
import sys
import config
import psycopg2


#Third Party
from datetime import datetime, date
from configparser import ConfigParser



class Info():
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

    def config(filename='database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(filename)

        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for params in params:
                db[param[0]] = param[1]
            else:
                raise Exception('Section {0} not found in the {1} file'.format(section, filename))
        return db

    def connect():
        conn = None

        try:
            params = self.config()

            print('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            print('PostgreSQL database version:')
            cur.execute('SELECT version()')

            db_version = cur.fetchone()
            print(db_version)

            cur.close()
        except(Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
                print('Database connection closed.')

# Main Function
if __name__ == "__main__":
    temp = Info()
    temp.run()
    connect()
