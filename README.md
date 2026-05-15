
# SkyGaser

## Weather, sky conditions and data Display

This project is a continuation of an earlier project, listed in my Github repository as "Dakota".  This
is similar, but the code is much improved and the data display presented is densor, but easier to read.


Uses Titano PyPortal hardware from Adafruit, http://www.adafruit.com,
along with an Adafruit BME280 I2C or SPI Temperature Humidity Pressure Sensor and
a Adafruit PCF8523 Real Time Clock Breakout Board.

**Written: 2026 by Rob**, rob@hafernik.com

This project is a real-time display of date, time, weather and sky conditions (see photo)

## Why?

So why work on a device that does nothing that a smart phone won't do?  Fair question.  Short hacker answer: 
because I can. There are other reasons, however. A person doesn't always have their phone on hand.  
The target location for this device is the bathroom of our house, where we've had one version or another 
of this device for several years and found it to be very helpful.  When you get up in the morning or middle of the night, you don't have 
our phone in your hand.  It's also a gentile nightlight.  In addition, it was a good way to stretch my hardware and 
programming skills.  I'vve never done any 3-D printing before, so this was a stretch.  Lastly, it's an excercise in 
UI/UX design.  So, plenty of *why*.

## UI/UX

Long experience with similar devices have informed the design of this one.  There are a few requirements:

- Time and temperature must be readable across the room (and from the shower) and distinct from each other
- Relative humidity and outside conditions should be clear and eaay to read
- UV index, moon phases, Air Quality Index, etc should be presented as easy to read graphics.
- Day of the week and month should be apparent.
- Inside conditions should include temperature, humidity and pressure.
- Weather alerts should show up prominenently.
- All data should be color coded such that general status (good, medium, bad) can be read at a distance.

These requirements led to the display you see in the project photos.

The Titano PyPortal has a Neopixel LED on the back.  Since this project has an enclosure, I wasn't
sure how to use it.  However, it turned out that the case is pretty reflective and the glow of the 
LED leaks around to the front.  To use this, I set the LED to yellow for a situation where Dakota 
isn't connected to the internet and red if there is a weather alert (which also displays on the LCD).

The backlight is set to the minimum I could set it to (lower values seem to turn it off altogether) when 
the light sensor detects dim light.  When it's not dim, the backlight is set to a moderately high value.  
This works better than I expected.

## Hardware

This project uses the **Titano** board from Adafruit.  

https://www.adafruit.com/product/4444

The Titano PyPortal uses an ATMEL (Microchip) ATSAMD51J20, and an 
Espressif ESP32 Wi-Fi coprocessor with TLS/SSL support built-in. It has a 3.5" diagonal 320 x 480 
color TFT with resistive touch screen (the touch interface is not used in this project).  It can be programmed
in CircuitPython, Adafruit's embedded Python environment.

Also in this project is a BME280 Temperature/Humidity/Pressure sensor and a PCF8523 Real Time Clock.  Both of these 
are easily available from Adafruit, Digi and so on.

Both the clock and sensor are I2C, meaning no soldering is required for this project.

## Theory of Operation

The code runs a loop every MAIN_SLEEP seconds (currently 10 seconds).  This means that the time displayed
(which is only hours and minutes) may be off by as much as MAIN_SLEEP seconds, but that is deemed OK for 
this particular application (it only shows hours and minutes anyway).

A pattern is followed that is common with CircuitPython: a "secrets.py" file is installed in the 
file system of the device.  This file is imported by the main file to get "secrets", such as the
WiFi password and other configuration.  A dummy of this file with no secrets is saved in the code
directory. This keeps the secrets from getting checked in to GitHub.   The real secrets file lives
only in the file system of the device.

All of the data collected from APIs and sensors is stored in a single Dictionary (also known as an associative array) called
**Data**.  Updating each type of data updates the map.  When it's time to draw the display, the
Data dictionary supplies all of the information.  This means that the APIs or sensors can be
swapped out withut major change to the code.  As long as they update the dictionary with the
same data, the display of the data is unchanged.  Conversely, changes to the design of 
the UI will not change the way that data is collected.  It's probably not "pythonic" to 
do it this way, but I'm old and set in my ways and that means a clear dividing line between
data and its display.

I spent a ridiculous amount of time trying to get the time right.  You would think time is an easy thing, 
but it is harder than it seems.  For one thing, the RTC does not do daylight savings time or time zones.
Also, the internal clock of the Titano is laughably inaccurate.  It would be off by minutes per day, if
you used it.  In the end, the only thing that seemed reliable was to keep the RTC tuned to UTC and then
apply an offset based on time zone and daylight savings time for display.  The time zone is set in the
secrets.py file, along with a flag indicating if daylight savings is in use in the locale where the 
SkyGaser is deployed.  From these, the time is adjusted from UTC to local time.  Since some of the APIs 
use Unix time (such as sunrise and sunset times), Unix time must be calculated from UTC, but this is
fairly straightforward.  All of these calculations could be improved, as far as performance goes, using
lookup tables and precalculated offsets, but the project is low on memory and this seems to fit OK.

A number of colors, such as "MODERATE" are used in the code.  I've found tha these are very subjective and YMMV.
Also, a given set of colors may not display quite the same on another device, even of the same manufacture.  
Obviously, if these don't look good to you, then use ones that do.  Also, I'm not a graphic designer, so my
colors may not harmonize in ways that designers like.

**Main Loop**

Each source of data for the program is obtained on its own schedule.  For example, the weather API is
called every WEATHER_FREQ seconds (currently 601, or about 10 minutes).  The code keeps a counter, called 
Tick, which is the Python time.time() result, which returns the hardware clock's number of seconds
since startup.  Each function keeps a counter and when the value of Tick exceeds the counter, it's 
time to perform the function.  The interval for each function is a prime number, meaning that the 
various function calls will very rarely line up and cause two functions to be performed in one loop.
This is a totally unnecessary frill, but I like primes.

Each time through the main loop, the code does the following:

* See if the device is connected to the WiFi access point.  If not connected, try to connect. If connected:
	- Get the weather, if it's time
	- Get the Air Quality Index, if it's time
* Get data from the SCD-30 sensor, if it's time
* Work out the Local Time, based on the RTC
* Show all of the data on the screen

**Displayed Data**

Here's what the SkyGaser displays:

- Current conditions, temperature, humidity and sky conditions.
- Today's forecast, straight from the API (which is sometimes worded funny, but what can you do?).  After
5PM it changes to tomorrow's forecast.
- Wind speed and direction, with North being up, of course.
- UV danger, with color going from deep blue (no danger at all), to bright purple (wear protection)
- Air quanlity, going from green (great) to bright yellow (very bad), with most important pollutant 
(eg, "O3" for ozone) in the middle.
- Moon phase (only showing the eight major phases, NOT an exact daily percentage).
- Inside conditions, from sensor (temperature, humidity, pressure -- same as outside).
- debug info (too dim to see easily).  Hours since reboot and free memory (see memory section).
- Day, date and time.
- Fortune cookie (stolen from old Unix box many years ago).  You can add or subtract your own by editing
the cookies.txt file.  This changes every 30 minutes.

**Memory and Circuit Python**

CircuitPython is tricky when it comes to memory.  Yes, it does have dynamically allocated memory, but 
NO, it does not have compaction.  *Memory can become fragmented.*  Since this projects involves calling APIs 
that may return 10-15K bytes of results (the weather alerts API can be bad about this), it needs that 
much contiguous memory.  It's important to kill off used memory as soon as possible to minimize fragmentation.
*I wish someone would put memory compaction into CircuitPython.  It's slow, I know, and would be terrible 
for a real-time system, but many projects, such as this one, would have no problem giving up a couple
of seconds now and then to compact memory.  It could be a call-on-demand feature, rather than automatic.*

**Networking**

Networking is hard on any microcontroller and the Titano is no exception.  In general, I've found that
long-running connections are not good and dropped connections to the WiFi network must be taken in stride. 
It's best to close connections and dispose of memory as soon as possible.  It's also important to *update the 
Titano to the newest firmware.  Adafruit has instructions for this and it certainly makes a difference.
The older stack will cause the device to need a reboot every 12 hours or so, whereas the latest libraries 
only require a reboot in some weeks' time.*

See this page:  https://learn.adafruit.com/upgrading-esp32-firmware/upgrade-all-in-one-esp32-airlift-firmware

It's also important to use the lastest version of CircuitPython and the latest version of the CircuitPython 
libraries.  These can be downloaded from Adafruit and other sources.

### OpenWeatherMap

The program uses the OpenWeatherMap APIs for weather and air quality information:

https://openweathermap.org

This is a wonderfull resource for weather information.  This code uses a paid API (although the payment only 
amounts to $2 or $3 per month), but it is perfectly possible to do similar things with completely free
information.  The APIs are clear, easy to call and well documented.  I *have* found that UV Index and 
Air Quality Index don't seem particularly meticulous, but I'm not a meteorologist, so what do I know?

Visit their website and follow the instructions to get an API Token.  This is a string of text you wlll 
need to add to your secrets.py file.

### Libraries

This project's lib/ directory will need the following from the Adafruit library sources:

adafruit_bitmap_font  
adafruit_display_shapes  
adafruit_requests.mpy  
adafruit_bme280  
adafruit_esp32spi  
adafruit_ticks.mpy  
adafruit_bus_device  
adafruit_imageload  
pcf8523.mpy  
adafruit_connection_manager.mpy  
adafruit_register  

### Resiliency

I've tried to make the code resilient to the most common problems: power failures, temporary internet
outages and so on.  These conditions are hard to test, however, and there is no doubt room for improvement.
Also, I've tried to make the failure of one thing not pull down everything else.  If the call to the
Air Quality API fails, for example, everything else will still get by with "--" shown for the
Air Quality.  Again, this leads to many combinations which are hard to test and there are likely
bugs to be fixed.

The SkyGaser runs for more than a week without reboot, which is fine for this use case
(the device is only out of service for 20-30 seconds on rreboot).

### Case

The case is 3D printed, from the two files included in the project .  I started with the case by joeyC (thanks!) 
and modified it to have a place for the temperature sensor.  Since you can't put the sensor in the case with the 
Titano (too much heat messes up the readings), I added a little sidecar to hold the temperature sensor.  I'm a 
newbie at 3-D printing, though, so my mods are probably awkward. The current case seems to work, but the temerature 
isolation between the Titano to the temperature sensor is still not perfect.

## License

Released under MIT license, see license file in repository.


