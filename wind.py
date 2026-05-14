# this module holds stuff ralated to displayintg wind speed and direction

import displayio

from adafruit_display_shapes.polygon import Polygon
from adafruit_display_text import label

WIND_SPEED_COLOR = (220,220,220)
ARROW_COLOR = 0xCCCCCC

arrows = {}

wind_speed_label = None
wind_group = None
current_arrow = None

# initialize display.  Eight wind directions are enough for this display
def setup(box_x, box_y, font):
	global wind_group
	global wind_speed_label
	global current_arrow

	# north
	arrows['north'] = Polygon([(30,62),(30,2),(30,62),(35,52),(25,52)], outline=ARROW_COLOR) #

	# northeast
	arrows['northeast'] = Polygon([(9,53),(51,11),(9,53),(9,43),(19,53)], outline=ARROW_COLOR) #

	# east
	arrows['east'] = Polygon([(0,32),(60,32),(0,32),(10,27),(10,37)], outline=ARROW_COLOR) #

	# southeast
	arrows['southeast'] = Polygon([(9,11),(51,53),(9,11),(19,11),(9,21)], outline=ARROW_COLOR) #

	# south
	arrows['south'] = Polygon([(30,2),(30,62),(30,2),(35,12),(25,12)], outline=ARROW_COLOR) #

 	# southwest
	arrows['southwest'] = Polygon([(51,11),(9,53),(51,11),(51,21),(41,11)], outline=ARROW_COLOR) #

	# west
	arrows['west'] = Polygon([(60,32),(0,32),(60,32),(55,27),(55,37)], outline=ARROW_COLOR) #

	# northwest
	arrows['northwest'] = Polygon([(51,53),(9,11),(51,53),(51,43),(41,53)], outline=ARROW_COLOR)

	current_arrow = None

	# wind speed label
	wind_speed_label = label.Label(font, text="0", color=WIND_SPEED_COLOR)
	wind_speed_label.anchor_point = (0.5, 0.0)
	wind_speed_label.anchored_position = (30, 22)

	# make a group to hold this view
	wind_group = displayio.Group(x=box_x, y=box_y)

	# append label to group
	wind_group.append(wind_speed_label)

	return wind_group

# update the wind group
def update(data):
	global wind_group
	global current_arrow

	try:
		# get data
		wind_speed = data['wind_speed']
		wind_speed_str = str(wind_speed)
		wind_dir_str = get_wind_dir_str(data['wind_dir']) # remember: this is FROM direction, not TO
		
		# if wind is zero, display a string
		if wind_speed == 0:
			wind_speed_str = "calm"

		# update label
		if wind_speed_label.text != wind_speed_str:
			wind_speed_label.text = wind_speed_str

		# remove current arrow, if any
		if current_arrow != None:
			wind_group.remove(current_arrow)

		# add new arrow, if there is wind
		if wind_speed > 0:
			current_arrow = arrows[wind_dir_str]
			wind_group.append(current_arrow)
		else:
			current_arrow = None

	except Exception as e:
		print ("**** Exception updating wind:", e, wind_dir_str)

# convert the wind direction to an approximate string 
def get_wind_dir_str(wind_dir):

	# print("wind_dir: ", wind_dir, type(wind_dir))
	wind_dir_str = ""
	if wind_dir >= 0 and wind_dir < 23:
		wind_dir_str = "north"
	elif wind_dir >= 23 and wind_dir < 68:
		wind_dir_str = "northeast"
	elif wind_dir >= 68 and wind_dir < 113:
		wind_dir_str = "east"
	elif wind_dir >= 113 and wind_dir < 158:
		wind_dir_str = "southeast"
	elif wind_dir >= 158 and wind_dir < 203:
		wind_dir_str = "south"
	elif wind_dir >= 203 and wind_dir < 248:
		wind_dir_str = "southwest"
	elif wind_dir >= 248 and wind_dir < 293:
		wind_dir_str = "west"
	elif wind_dir >= 293 and wind_dir < 338:
		wind_dir_str = "northwest"
	elif wind_dir >= 338:
		wind_dir_str = "north"

	return wind_dir_str
