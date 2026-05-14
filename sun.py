# this module holds stuff ralated to displayintg sun mode and UV

import board

import displayio

from adafruit_display_shapes.circle import Circle
from adafruit_display_text import label
from adafruit_display_shapes.line import Line

# sun outline circle colors
SUN_DAY_CIRCLE_COLOR = 0xDDDD00
SUN_NIGHT_CIRCLE_COLOR = 0x444444

SUNRISE_HORIZON_COLOR = 0xF0C828
SUNSET_HORIZON_COLOR = 0xF06428

# sun text color for various modes
SUNRISE_TEXT_COLOR = (240,200,40)  # f0c828
SUNSET_TEXT_COLOR = (240,100,40)  # f06428
SUN_NIGHT_TEXT_COLOR = (0,0,0)

# UV Index colors
UV_GOOD_COLOR = (0,0,160)
UV_FAIR_COLOR = (80,20,240)
UV_MODERATE_COLOR = (160,20,240)
UV_BAD_COLOR = (240,100,240)
UV_HORRIBLE_COLOR = (250,200,250)

sun_circle_1 = None
sun_circle_2 = None
sun_circle_3 = None

sunrise_horizon_1 = None
sunrise_horizon_2 = None

sunset_horizon_1 = None
sunset_horizon_2 = None

current_horizon_1 = None
current_horizon_2 = None

old_sun_mode = None
sun_label = None
sun_group = None

# sun modes
SUN_RISE = 1
SUN_SET = 2
SUN_DAY = 3
SUN_NIGHT = 4

##### setup display.
def setup(box_x, box_y, font):
	global sun_circle_1
	global sun_circle_2
	global sun_circle_3

	global sunrise_horizon_1
	global sunrise_horizon_2

	global sunset_horizon_1
	global sunset_horizon_2

	global old_sun_mode
	global sun_label
	global sun_group

	sun_circle_1 = Circle(x0=30,y0=31,r=31,outline=SUN_DAY_CIRCLE_COLOR)
	sun_circle_2 = Circle(x0=30,y0=31,r=30,outline=SUN_DAY_CIRCLE_COLOR)
	sun_circle_3 = Circle(x0=30,y0=31,r=29,outline=SUN_DAY_CIRCLE_COLOR)

	sunrise_horizon_1 = Line(2, 0, 60, 0, SUNRISE_HORIZON_COLOR)
	sunrise_horizon_2 = Line(2, 1, 60, 1, SUNRISE_HORIZON_COLOR)

	sunset_horizon_1 = Line(2, 62, 60, 62, SUNSET_HORIZON_COLOR)
	sunset_horizon_2 = Line(2, 63, 60, 63, SUNSET_HORIZON_COLOR)

	sun_label = label.Label(font, text="UV", color=SUNSET_TEXT_COLOR)
	sun_label.anchor_point = (0.5, 0.0)
	sun_label.anchored_position = (30, 22)

	old_sun_mode = 0 # start with no old sun mode

	sun_group = displayio.Group(x=box_x, y=box_y)

	# append label and sun circle to group
	sun_group.append(sun_circle_1)
	sun_group.append(sun_circle_2)
	sun_group.append(sun_circle_3)
	sun_group.append(sun_label)

	return sun_group

##### Update sun group
def update(data):
	global current_horizon_1
	global current_horizon_2
	global old_sun_mode

	try:
		new_sun_mode = get_sun_mode(data['sunrise_delta'], data['sunset_delta'])

		# if it's a new mode, we have to erase and draw
		if new_sun_mode != old_sun_mode:

			# remove horizon lines to get ready for new mode
			try:
				if current_horizon_1 != None:
					sun_group.remove(current_horizon_1)
					current_horizon_1 = None
				if current_horizon_2 != None:
					sun_group.remove(current_horizon_2)
					current_horizon_2 = None
			except Exception as ee:
				print ("**** Exception removing horizon lines: ", ee)

			# add thinga for the new mode, if mode needs it
			if new_sun_mode == SUN_RISE:
				sun_group.append(sunrise_horizon_1)
				sun_group.append(sunrise_horizon_2)
				current_horizon_1 = sunrise_horizon_1
				current_horizon_2 = sunrise_horizon_2

				sun_circle_1.outline = SUN_DAY_CIRCLE_COLOR
				sun_circle_2.outline = SUN_DAY_CIRCLE_COLOR
				sun_circle_3.outline = SUN_DAY_CIRCLE_COLOR

			elif new_sun_mode == SUN_SET:
				sun_group.append(sunset_horizon_1)
				sun_group.append(sunset_horizon_2)
				current_horizon_1 = sunset_horizon_1
				current_horizon_2 = sunset_horizon_2

				sun_circle_1.outline = SUN_DAY_CIRCLE_COLOR
				sun_circle_2.outline = SUN_DAY_CIRCLE_COLOR
				sun_circle_3.outline = SUN_DAY_CIRCLE_COLOR

			elif new_sun_mode == SUN_DAY:
				sun_circle_1.outline = SUN_DAY_CIRCLE_COLOR
				sun_circle_2.outline = SUN_DAY_CIRCLE_COLOR
				sun_circle_3.outline = SUN_DAY_CIRCLE_COLOR

			elif new_sun_mode == SUN_NIGHT:
				sun_circle_1.outline = SUN_NIGHT_CIRCLE_COLOR
				sun_circle_2.outline = SUN_NIGHT_CIRCLE_COLOR
				sun_circle_3.outline = SUN_NIGHT_CIRCLE_COLOR

		# update the sun label according to mode
		if new_sun_mode == SUN_NIGHT:
			# just dark at night
			sun_label.color = SUN_NIGHT_TEXT_COLOR

		elif new_sun_mode == SUN_RISE:
			# update sun rise time, avoid displaying "0" minutes due to rounding
			sr_mins = round(data['sunrise_delta'] / 60)
			sunrise_min = ""
			if sr_mins >= 1:
				sunrise_min = str(sr_mins)

			if sun_label.text != sunrise_min:
				sun_label.text = sunrise_min
				sun_label.color = SUNRISE_TEXT_COLOR

		elif new_sun_mode == SUN_SET:
			# update sun set time
			ss_mins = round(data['sunset_delta'] / 60)
			sunset_min = ""
			if ss_mins >= 1:
				sunset_min = str(ss_mins)

			if sun_label.text != sunset_min:
				sun_label.text = sunset_min
				sun_label.color = SUNSET_TEXT_COLOR

		elif new_sun_mode == SUN_DAY:
			# during the day update the UV indicator
			if(sun_label.text != "UV"):
				sun_label.text = "UV"
			sun_label.color = get_uvi_color(data['uv_index'])  # day sun gets UV color...

		old_sun_mode = new_sun_mode

		board.DISPLAY.refresh()

	except Exception as e:
		print ("**** Exception updating sun:", e)


##### get UVI color (scalled according to API docs)
def get_uvi_color(uvi):
    # Define UVI ranges and corresponding colors
    uvi_ranges = [
        (10.0, UV_HORRIBLE_COLOR),
        (7.0, UV_BAD_COLOR),
        (5.0, UV_MODERATE_COLOR),
        (2.0, UV_FAIR_COLOR)
    ]

    # Determine the color based on UVI value
    for threshold, color in uvi_ranges:
        if uvi > threshold:
            return color

    return UV_GOOD_COLOR

##### get the sun mode, ie, what to display for the sun
#####  (dependent on API representation of sunrise and sunset)
def get_sun_mode(time_to_sunrise, time_to_sunset):
	sm = SUN_NIGHT

	# if it's less than an hour to sunrise
	if time_to_sunrise > 0 and time_to_sunrise < 3600:
		sm = SUN_RISE

	# if it's less than an hour to sunset
	elif time_to_sunset > 0 and time_to_sunset < 3600:
		sm = SUN_SET

	# else if it's daytime
	elif time_to_sunrise < 0 and time_to_sunset > 0:
		sm = SUN_DAY

	# print ("---- Sun mode: ", time_to_sunrise, ", ", time_to_sunset, ": ", sm)
	return sm
