#
#   This code drives a device that presents a data screen that contains weather, date, time, air quality, astronomical data, etc
#
#   Rob Hafernik, rob@hafernik.com  
#

import busio
import time
import board
import pcf8523
import gc
import time
import board
import random
import microcontroller
import traceback
import displayio
import neopixel

from digitalio import DigitalInOut
from analogio import AnalogIn

import adafruit_requests
import adafruit_connection_manager

from adafruit_bitmap_font import bitmap_font
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_bme280 import basic as adafruit_bme280

from microcontroller import watchdog
from watchdog import WatchDogMode

# all the parts of our display
import conditions
import alerts
import wind
import sun
import air_quality
import moon_phase
import other_weather
import date_time
import cookie

##############################################################
# Main loop: where the action is...  called every LOOP_SLEEP seconds
##############################################################
def main():
    global Data
    global Display_group
    global LastWeather
    global LastAQI
    global LastSensor
    global LastCookie
    global LastComms

    # fix up time values
    now = fix_time()  # might be wrong, since API hasn't been called yet
    Data['uptime'] = now - Data['boot_time']

    # feed the watchdog timer to keep it from expiring
    watchdog_timer.feed()
    gc.collect()

    # make sure we're connected
    connect_to_wifi()
    watchdog_timer.feed()
    time.sleep(1.0)

    # is it time to call the weather API?
    if (now - LastWeather) > WEATHER_FREQ:
        if call_weather_api(now) == True:
            LastWeather = now

    # is it time to call the AQI API?
    if (now - LastAQI) > AIRQUALITY_FREQ:
        if call_aqi_api() == True:
            LastAQI = now

    # is it time to read in a new fortune cookie?
    if (now - LastCookie) > COOKIE_FREQ:
        read_cookie()
        LastCookie = now

    # read sensor every loop, it costs nothing 
    read_sensor()

    # get ready to draw
    fix_weather()

    # put our house in order as much as possible
    watchdog_timer.feed()
    gc.collect()

    # draw to screen
    date_time.update(Data)
    conditions.update(Data)
    alerts.update(Data)
    wind.update(Data)
    sun.update(Data)
    air_quality.update(Data)
    moon_phase.update(Data)
    other_weather.update(Data)
    cookie.update(Data)

    # just for debugging...
    print("%s %s %s" % (Data['day_of_week'], Data['month'], Data['day_of_month']), "%s:%0s" % (Data['hour'], Data['minute']), " - ", now, " . ", (now-LastComms), " . ", Data['uptime'], " - ", gc.mem_free())
#        print("Outdoors:", Data['temp'], "F,", Data['humidity'], "%,", Data['pressure'], "mb")
#        print("Indoors: ", Data['indoor_temp'], "F,", Data['indoor_humidity'], "%,", Data['indoor_pressure'], "mb / ", Data['indoor_pressure'], "mb")
#        print("Alerts:  ", Data['weather_alert_1'], ",", Data['weather_alert_2'], "   ", Data['show_alerts'] )
##       print("Sunrise: ", Data['sunrise'], ".", Data['sunrise_delta'], ",  Sunset: ", Data['sunset'], ".", Data['sunset_delta'], ", Moon: ", Data['moon_phase'])
#        print("AQI:     ", Data['aqi_index'], Data['aqi_co'], Data['aqi_no'], Data['aqi_no2'], Data['aqi_o3'], Data['aqi_so2'], Data['aqi_pm2_5'], Data['aqi_pm10'], Data['aqi_nh3'])
#        print("Cookie:  ", Data['cookie'])

    now = fix_time()
    
    # set backlight, else it's too bright at night
    set_backlight()

########## try to connect, but only if not connected.
def connect_to_wifi():
    watchdog_timer.feed()

    if not Radio.is_connected:
        set_warning_level(YELLOW_ALERT)
        print("++  connecting to WiFi...")
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                Radio.connect_AP(SSID, PASSWORD)
                
                # === CRITICAL FIX: Re-create fresh pool and session ===
                global Pool, Ssl_context, Requests
                Pool = adafruit_connection_manager.get_radio_socketpool(Radio)
                Ssl_context = adafruit_connection_manager.get_radio_ssl_context(Radio)
                Requests = adafruit_requests.Session(Pool, Ssl_context)
                
                time.sleep(0.5)  # Reduced from 1s — fresh session makes it settle faster
                
                if Radio.is_connected:
                    rssi_val = Radio.rssi if hasattr(Radio, 'rssi') else "unknown"
                    print(f"++  connected to {SSID} \tRSSI: {rssi_val}")
                    set_warning_level(ALLGOOD)
                    return True
                else:
                    print("Connect call succeeded but is_connected=False")
            except RuntimeError as e:
                print(f"!!!!! Attempt {attempts+1}/{max_attempts} failed: {e}")
                print(f"Status: {Radio.status if hasattr(Radio, 'status') else 'N/A'}")
            attempts += 1
            time.sleep(2)
        
        print("!!!!! Failed to connect after retries")
        set_warning_level(RED_ALERT)
        return False
    else:
        return True

########## Call API and set RTC with results
def set_time_from_api():
    global LastComms
    print("++  Attempting time API...")

    max_retries = 8
    for attempt in range(max_retries):
        try:
            with Requests.get(TIME_API_URL, timeout=10) as r:
                if r.status_code == 200:
                    time_json = r.json()                    # safely parse JSON

                    unix_time = time_json.get("timestamp") or time_json.get("unixtime")
                    if unix_time is None:
                        print("No timestamp key found")
                        continue

                    unix_time = int(unix_time)

                    # === Use localtime (your build doesn't have gmtime) ===
                    Rtc.datetime = time.localtime(unix_time)

                    LastComms = fix_time()
                    print(f"++  Time synced! Unix={unix_time}  RTC={Rtc.datetime}")
                    return True

                else:
                    print(f"!!!!! Bad status from time API: {r.status_code}")

        except Exception as e:
            print(f"Time API attempt {attempt+1} failed: {e}")

        time.sleep(3)

    print("!!!!! Time API failed after all retries")
    return False

########## US DST rules (2007–present) based on UTC time 
########## Lots of magic here, based on US govt rules for DST
########## transition days cached to save CPU cycles the rest of the time
def is_current_dst(t):
    """Returns True if DST is currently in effect (UTC time from RTC)."""
    if not OBSERVE_DST:
        return False

    year = t.tm_year
    month = t.tm_mon
    day = t.tm_mday
    hour = t.tm_hour

    # Cache transition days in Data so we only calculate once per year
    if Data.get('dst_year') != year:
        Data['dst_year'] = year
        Data['dst_march'] = second_sunday_march(year)   # day number in March
        Data['dst_nov']   = first_sunday_november(year) # day number in Nov

    # Quick month checks
    if month < 3 or month > 11:
        return False
    if 3 < month < 11:
        return True

    # March transition
    if month == 3:
        if day < Data['dst_march']:
            return False
        if day > Data['dst_march']:
            return True
        return hour >= 2   # 2 AM local

    # November transition
    if month == 11:
        if day < Data['dst_nov']:
            return True
        if day > Data['dst_nov']:
            return False
        return hour < 2    # before 2 AM local

    return False


# Helper functions (called only when year changes)
def second_sunday_march(year):
    # Find weekday of March 1 (0=Mon ... 6=Sun)
    march1 = time.mktime(time.struct_time((year, 3, 1, 0, 0, 0, -1, -1, -1)))
    wd = time.localtime(march1).tm_wday
    days_to_sunday = (6 - wd) % 7
    first_sunday = 1 + days_to_sunday
    return first_sunday + 7   # second Sunday


def first_sunday_november(year):
    nov1 = time.mktime(time.struct_time((year, 11, 1, 0, 0, 0, -1, -1, -1)))
    wd = time.localtime(nov1).tm_wday
    days_to_sunday = (6 - wd) % 7
    return 1 + days_to_sunday

########## Use RTC to grab current time, "fix" it in Data object and return unix time (for use with APIs, such as weather alert times)
########## The RTC doesn't keep time zone or daylight savings time.  It just keeps hours, minutes, seconds and so on.  
def fix_time():
    t = get_local_time()

    try:
        dow_index = t.tm_wday          # 0=Mon ... 6=Sun
        Data['day_of_week'] = DAY_OF_WEEK[dow_index]
        Data['month'] = MONTH_ABBR[t.tm_mon]
        Data['day_of_month'] = t.tm_mday
        Data['hour'] = t.tm_hour
        Data['minute'] = t.tm_min
    except Exception as e:
        print("fix_time error:", e, t)
        Data['day_of_week'] = "???"
        Data['month'] = "???"
        Data['day_of_month'] = 0
        Data['hour'] = 0
        Data['minute'] = 0

    return get_unix_time()

########## Always returns true Unix time (UTC seconds), based on value in RTC ##########
def get_unix_time():
    t = Rtc.datetime
    if t.tm_year < 2020 or t.tm_year > 2050:
        print("!!!!! RTC time looks invalid:", t)
        return 0
    return time.mktime(t)   # RTC is now UTC → this is real Unix time

########## Convert current UTC (from RTC) → local time for display ##########
def get_local_time():
    unix = get_unix_time()
    utc_t = Rtc.datetime

    dst = is_current_dst(utc_t)
    offset_hours = TZ_OFFSET + (1 if dst else 0)   # TZ_OFFSET is from secrets file

    local_unix = unix + (offset_hours * 3600)      # ← Add (because offset is negative)

    return time.localtime(local_unix)

########## parse a date-time as found in some APIs
def parse_datetime(datetime_string):
    # Split the string into date and time parts
    date_part, time_part = datetime_string.split('T')
    
    # Parse date
    year, month, day = map(int, date_part.split('-'))
    
    # Parse time (ignore milliseconds and timezone)
    time_part = time_part.split('.')[0]  # Remove milliseconds
    hour, minute, second = map(int, time_part.split(':'))
    
    return (year, month, day, hour, minute, second)

########## read data from sensor
def read_sensor():
    global Bme280

    clear_sensor_data()

    if Bme280 != None:
        t = int(round(convert_ctof(Bme280.temperature + TEMP_CALIBRATION)))
        h = int(round(Bme280.humidity + HUMIDITY_CALIBRATION))
        p = int(round(Bme280.pressure + PRESSURE_CALIBRATION))

        Data['indoor_temp'] = t
        Data['indoor_humidity'] = h
        Data['indoor_pressure'] = p

########## call weather api
def call_weather_api(unix_time):
    global LastComms
    succeeded = False

    try:

        with Requests.get(OPEN_WEATHER_URL) as weather_response:

            if weather_response.status_code == 200:
            
                clear_weather()
    
                # if it's after 17:00, show tomorrow's forcast, else show today's
                day_index = 0   # today
                prefix = "Today  "
                if Data['hour'] != None and int(Data['hour']) >= 17:
                    day_index = 1   # tomorrow
                    prefix = "Tomorrow  "

                #print ("hour " + Data['hour'] + "  " + str(day_index))

                # call the API
                rjson = weather_response.json()
                current = rjson['current']
                today = rjson['daily'][0]
                daily = rjson['daily'][day_index]

                # get all the other weather stuff
                Data['temp'] = round(convert_ktof(float(current['temp'])))
                Data['humidity'] = round(current['humidity'])
                Data['pressure'] = round(current['pressure'])
                Data['uv_index'] = float(current['uvi'])

                Data["sunrise"] = int(current['sunrise']) 
                Data["sunset"] = int(current['sunset'])

                Data['moon_phase'] = float(today['moon_phase'])

                Data['forecast_cond'] = daily['summary']
                forecast_min = round(convert_ktof(float(daily['temp']['min'])))
                forecast_max = round(convert_ktof(float(daily['temp']['max'])))

                Data['forecast_temps'] = prefix + "Hi: " + str(forecast_max) + "  Lo: " + str(forecast_min)

                # upper case the condition string (CircuitPython has no "capitalize()")
                #   strangely, this is a UI issue, the upper cased string actually helps
                c_str = current["weather"][0]["description"]
                cond_str = c_str[0].upper() + c_str[1:].lower()
                Data['conditions'] = cond_str   

                Data['wind_dir'] = int(current['wind_deg'])
                Data['wind_speed'] = convert_mpstomph(int(current['wind_speed']))

                # comms were successful and the API was called
                LastComms = fix_time()
                succeeded = True
                
                del rjson

                print("++  called weather conditions API")

            else:
                print("!!!!!  weather conditions API response code:", weather_response.status_code)

    except Exception as e:
        print("Exception getting weather: ", e)

    # now check for weather alerts
    try:
        with Requests.get(OPEN_WEATHER_ALERTS_URL) as weather_response:
            if weather_response.status_code == 200:
                rjson = weather_response.json()

                Data['weather_alert_1'] = ""
                Data['weather_alert_2'] = ""
                Data['show_alerts'] = False

                if rjson.get('alerts'):
                    alerts = rjson['alerts']

                    active_alerts = []
                    current_time = get_unix_time(Rtc.datetime)  # your unix time helper

                    for a in alerts:
                        start = a.get('start', 0)
                        end = a.get('end', 9999999999)
                        if start <= current_time <= end:
                            # Prefer short event name
                            short_text = a.get('event', '').strip()
                            if not short_text:
                                short_text = "Weather Alert"  # fallback

                            # Optional: truncate if ridiculously long (rare)
                            if len(short_text) > 40:
                                short_text = short_text[:37] + "..."

                            active_alerts.append(short_text)

                    # Take first two (your UI limit)
                    if active_alerts:
                        Data['weather_alert_1'] = active_alerts[0]
                        Data['show_alerts'] = True
                        if len(active_alerts) > 1:
                            Data['weather_alert_2'] = active_alerts[1]

                # LED and cleanup
                if Data['show_alerts']:
                    set_warning_level(RED_ALERT)
                else:
                    set_warning_level(ALLGOOD)

                del rjson           # free the big JSON immediately
                gc.collect()        # reclaim memory NOW

                print("++  called weather alerts API")

            else:
                print("!!!!!  weather alerts API response code:", weather_response.status_code)

    except Exception as e:
        print("Exception getting weather alerts:", e)

    gc.collect()
    return succeeded

########## do calculations related time-sensitive weather data, such as sunrise and sunset
########## fix the results into the Data object
def fix_weather():
    unix_time = get_unix_time()

    sunruse_delta = Data['sunrise'] - unix_time                # difference between now and sunrise today.  may be negative
    Data['sunrise_delta'] = sunruse_delta
    sunset_delta = Data['sunset'] - unix_time                  # difference between now and sunset today.  may be negative
    Data['sunset_delta'] = sunset_delta 

########## call the air quality API
def call_aqi_api():
    global LastComms
    succeeded = False

    try:

        with Requests.get(OPEN_WEATHER_AQI_URL) as aqi_response:

            if aqi_response.status_code == 200:

                clear_aqi()
                
                rjson = aqi_response.json()

                size = len(rjson['list']) # should be just 1 item in list, but zero means "error, no data".
                if size > 0:
                    aq_index = rjson['list'][0]['main']['aqi']
                    aq_index = int(aq_index)
                    Data['aqi_index'] = aq_index
                    
                    Data['aqi_co'] = float(rjson['list'][0]['components']['co'])
                    Data['aqi_no'] = float(rjson['list'][0]['components']['no'])
                    Data['aqi_no2'] = float(rjson['list'][0]['components']['no2'])
                    Data['aqi_o3'] = float(rjson['list'][0]['components']['o3'])
                    Data['aqi_so2'] = float(rjson['list'][0]['components']['so2'])
                    Data['aqi_pm2_5'] = float(rjson['list'][0]['components']['pm2_5'])
                    Data['aqi_pm10'] = float(rjson['list'][0]['components']['pm10'])
                    Data['aqi_nh3'] = float(rjson['list'][0]['components']['nh3'])

                # comms were successful
                LastComms = fix_time()
                succeeded = True

                del rjson
                
                print("++  called AQI API")

            else:
                print ("!!!!!  AQI API response code:",aqi_response.status_code)

    except Exception as e:
        print("Exception getting air quality: ", e)

    return succeeded

########## read a ramdon cookie from a cookie file, but only if there is plenty of memory for it
def read_cookie():

    try:
        clear_cookie()

        gc.collect()

        # use reservoir sampling (thanks, Jeffrey S. Vitter!) to pick a random line reading 
        # over the whole file.  Only reads one line into memory at a time, but always reads whole file
        chosen_line = NO_STR
        with open('cookies.txt', 'r') as file:
            for line_number, line in enumerate(file, start=1):
                if random.randint(1, line_number) == 1:
                    chosen_line = line.strip()  # Replace the chosen line with probability 1/line_number

        Data['cookie'] = chosen_line

        print("++  Loaded fortune cookie:", Data['cookie'])

        gc.collect() # free up the memory this used right away

    except Exception as e:
        print("!!!!!  Exception loading cookie: ", e)
        Data['cookie'] = "Exception loading cookie... no, really!"

########## set the backlight brightness, based on ambient light
def set_backlight():

    try:
        ambient = Light_Sensor.value
        Data['ambient'] = ambient            # just in case we want to use it elsewhere

        if ambient < 5000:                  
            board.DISPLAY.brightness = 0.45  # this light level works out to "dim, but not black"
        else:
            board.DISPLAY.brightness = 0.85  # good for all but direct sunlight

    except Exception as e:
        print("!!!!!  Exception seting backlight:", e)

########## convert kelvin to fahrenheit
def convert_ktof(k):
    k = ((k * 9.0)/5.0) - 459.67
    return k;

########## convert celcius to fahrenheit
def convert_ctof(c):
    f = (c * 1.8) + 32.0
    return f;

########## convert meters per second to miles per hour
def convert_mpstomph(mps):
    mphstr = round(mps * 2.237)
    return mphstr;

########## set the RGB pixel 
def set_warning_level(warn):
    Pixel[0] = warn
    return;

########## clear time
def clear_time():

    Data['day_of_week'] = NO_STR
    Data['day_of_month'] = 0
    Data['month'] = NO_STR
    Data['hour'] = 0
    Data['minute'] = 0

########## clear out Weather values
def clear_weather():

    Data['temp'] = 0
    Data['humidity'] = 0
    Data['pressure'] = 0
    Data['uv_index'] = 1
    Data['conditions'] = NO_STR
    Data['wind_dir'] = 0
    Data['wind_speed'] = 0.0
    Data['sunrise_delta'] = 0
    Data['sunset_delta'] = 0
    Data['show_alerts'] = False
    Data['forecast_temps'] = NO_STR
    Data['forecast_cond'] = NO_STR
    Data['weather_alert_1'] = NO_STR
    Data['weather_alert_2'] = NO_STR
    Data['sunrise'] = 0
    Data['sunset'] = 0

    Data['moon_phase'] = 0.0

########## clear sensor data
def clear_sensor_data():

    Data['indoor_temp'] = 0
    Data['indoor_humidity'] = 0
    Data['indoor_pressure'] = 0
    Data['indoor_co2'] = 0  # current sensor doesn't measure this

########## air quality data
def clear_aqi():

    Data['aqi_index'] = 1
    Data['aqi_co'] = None
    Data['aqi_no'] = None
    Data['aqi_no2'] = None
    Data['aqi_o3'] = None
    Data['aqi_so2'] = None
    Data['aqi_pm2_5'] = None
    Data['aqi_pm10'] = None
    Data['aqi_nh3'] = None

########## clear cookie
def clear_cookie():
    Data['cookie'] = NO_STR

########## hard reboot, for reasons
def reboot():
    print("!!!!!!!!!!!!!!!!!!!!!!! HARD RESET !!!!!!!!!!!!!!!!!!!!!!!")
    time.sleep(2.0)
    microcontroller.reset()

#################################################################

print("***** SkyGazer Starting Up *****")

##### Get our secrets
try:
    from secrets import secrets
except ImportError:
    print("!!!!! No secrets file")
    raise

SSID = secrets["ssid"]
PASSWORD = secrets["password"]
WEATHER_API_KEY = secrets["openweather_api_token"]
LATITUDE = secrets['Latitude']
LONGITUDE = secrets['Longitude']
TZ_OFFSET = secrets['TZ_OFFSET']
OBSERVE_DST = secrets['OBSERVE_DST']

##### Constants
TIME_API_URL = "https://aisenseapi.com/services/v1/timestamp"
#TIME_API_URL = 'http://worldtimeapi.org/api/timezone/America/Chicago'
OPEN_WEATHER_URL = "http://api.openweathermap.org/data/3.0/onecall?lat="+LATITUDE+"&lon="+LONGITUDE+"&exclude=hourly,minutely,alerts&appid="+WEATHER_API_KEY
OPEN_WEATHER_ALERTS_URL = "http://api.openweathermap.org/data/3.0/onecall?lat="+LATITUDE+"&lon="+LONGITUDE+"&exclude=daily,minutely,hourly,current&appid="+WEATHER_API_KEY
OPEN_WEATHER_AQI_URL = "http://api.openweathermap.org/data/2.5/air_pollution?lat="+LATITUDE+"&lon="+LONGITUDE+"&appid="+WEATHER_API_KEY

LOOP_SLEEP = 10             # how much to sleep in main loop, secs

NO_STR = ""
DAY_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_ABBR = [ "--", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ]

WEATHER_FREQ = 607          # conditions can change fast...
AIRQUALITY_FREQ = 5_109     # air quality does not change fast...
COOKIE_FREQ = 1_800         # load a new fortune cookie every 30 minutes
MAX_COMMS_FAILURE = 1_800   # max time to go without comms before a reboot happens

# These were determined empirically, relative to known good sources
# When the sensors change, these will have to be updated
TEMP_CALIBRATION = 0
HUMIDITY_CALIBRATION = -10
PRESSURE_CALIBRATION = 17   # correct for both altitude and sensor accuracy (determined using a known good source)
                            # will have to change at other altitudes

# Neopixel warning colors
ALLGOOD = (0, 0, 0)             # for the neopixel "all good" is "off"
YELLOW_ALERT = (128, 128, 0) 
RED_ALERT = (128, 0, 0)
RED_RED_ALERT = (240, 64, 64)

##### some globals
Data = {}
LastWeather = 0
LastAQI = 0
LastSensor = 0
LastCookie = 0
LastComms = 0

##### Networking setup
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

Spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
Radio = adafruit_esp32spi.ESP_SPIcontrol(Spi, esp32_cs, esp32_ready, esp32_reset)
Radio.set_dns_config("8.8.8.8", "8.8.4.4")

Pool = adafruit_connection_manager.get_radio_socketpool(Radio)
Ssl_context = adafruit_connection_manager.get_radio_ssl_context(Radio)
Requests = adafruit_requests.Session(Pool, Ssl_context)

##### setup for clock
myI2C = busio.I2C(board.SCL, board.SDA)
Rtc = pcf8523.PCF8523(myI2C)

##### setup for temp/humid sensor
Bme280 = adafruit_bme280.Adafruit_BME280_I2C(myI2C)

# setup for built-in light sensor
Light_Sensor = AnalogIn(board.LIGHT)

##### set up the neopixel
Pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, auto_write=True)
Pixel[0] = ALLGOOD


##### seed random number generator with light level...
random.seed(Light_Sensor.value)

# set up fonts
LgFont = bitmap_font.load_font("/fonts/Source_Sans_Pro_Bold-72.bdf")
MdFont = bitmap_font.load_font("/fonts/Source_Sans_Pro-32.bdf")
SmFont = bitmap_font.load_font("/fonts/Source_Sans_Pro-24.bdf")

##### this is an emergency back-up reboot in case the system freezes up
##### once the timer expires (the feed() method is no longer called), the system hard-reboots
watchdog_timer = watchdog
watchdog_timer.timeout = 16   # for some reason timeout must be <= 16
watchdog_timer.mode = WatchDogMode.RESET

##### blank slate
clear_time()
clear_weather()
clear_sensor_data()
clear_aqi()
clear_cookie()

##### set up display areas
Display_group = displayio.Group()
board.DISPLAY.root_group = Display_group

Display_group.append(conditions.setup(0, 0, MdFont, LgFont))
Display_group.append(alerts.setup(0, 77, SmFont))
Display_group.append(wind.setup(30, 124, MdFont))  # raised up a little due to wind direction vector...
Display_group.append(sun.setup(150, 126, MdFont))
Display_group.append(air_quality.setup(255, 126, MdFont))  # AQI display is 90px wide...
Display_group.append(moon_phase.setup(390, 126))
Display_group.append(other_weather.setup(0, 186, SmFont))
Display_group.append(date_time.setup(0, 226, MdFont, LgFont))
Display_group.append(cookie.setup(0, 304, SmFont))

##### show date and time before anything else (clock hasn't synched with internet yet, but that's probably OK)
fix_time()
date_time.update(Data)

##### connext to wifi, get our time stuff on track
connect_to_wifi()
time.sleep(2.0)                     # let the wifi driver code have time to settle down
fix_time()
set_time_from_api()                 # on start up, sych RTC to good time from the internet.
                                    #   RTC should be good within a minute a year or so after that.
now = fix_time()                    # fix time values, even if API call didn't work
Data['boot_time'] = now             # if API call failed, this could be off 
LastComms = now                     # assume comms are good at boot time
Data['uptime'] = 0                  # track uptime for quality control porpoises

##### main loop
while True: 
    try:
        main()

    except Exception as e:
        print("%s %s %s" % (Data['day_of_week'], Data['month'], Data['day_of_month']), "%s:%0s" % (Data['hour'], Data['minute']))
        print("@@@@@@@@@@ Exception in main loop: ", e)
        traceback.print_exception(e)
        reboot()

    watchdog_timer.feed()
    time.sleep(LOOP_SLEEP)

print("***** SkyGazer Done *****") # should never see this...

