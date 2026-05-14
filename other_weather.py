# labels that display other weather data

import displayio
import gc
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.line import Line

indoor_temp_label = None
indoor_humidity_label = None
co2_label = None
pressure_label = None

other_group = None

OTHER_GOOD_COLOR = (60,100,250)
OTHER_BAD_COLOR = (200,200,250)
MEM_COLOR = (40,40,40)
UPTIME_COLOR = (40,40,40)

def setup(box_x, box_y, font):
	global indoor_temp_label
	global indoor_humidity_label
	global mem_label
	global pressure_label
	global other_group
	global uptime_label

	# indoor temp
	indoor_temp_label = label.Label(font, text="-", color=OTHER_GOOD_COLOR, x=5, y=20)
	indoor_temp_label.base_alignment = True
	
	# inside humidity
	# indoor_humidity_label = bitmap_label.Label(font, text="-", color=OTHER_GOOD_COLOR, x=130, y=20)
	indoor_humidity_label = label.Label(font, text="-", color=OTHER_GOOD_COLOR, x=45, y=20)
	indoor_humidity_label.base_alignment = True

	# pressure
	pressure_label = label.Label(font, text="-", color=OTHER_GOOD_COLOR, x=100, y=20)
	pressure_label.base_alignment = True

	# uptime
	uptime_label = label.Label(font, text="-", color=UPTIME_COLOR, x=284, y=20)
	uptime_label.base_alignment = True

	# memory
	mem_label = label.Label(font, text="-", color=MEM_COLOR, x=390, y=20)
	mem_label.base_alignment = True

	other_group = displayio.Group(x=box_x, y=box_y)
	other_group.append(indoor_temp_label)
	other_group.append(indoor_humidity_label)
	other_group.append(mem_label)
	other_group.append(uptime_label)
	other_group.append(pressure_label)

	return other_group

def update(data):
	global indoor_temp_label
	global indoor_humidity_label
	global mem_label
	global pressure_label
	global other_group
	global uptime_label

	try:
		tval = data["indoor_temp"]
		tstr = str(tval)
		if indoor_temp_label.text != tstr:
			indoor_temp_label.text = tstr
		if tval > 79 or tval < 63:
			indoor_temp_label.color = OTHER_BAD_COLOR
		else:
			indoor_temp_label.color = OTHER_GOOD_COLOR

		hval = data["indoor_humidity"]
		hstr = str(hval) + "%"
		if indoor_humidity_label.text != hstr:
			indoor_humidity_label.text = hstr
		if hval > 80 or hval < 40:
			indoor_humidity_label.color = OTHER_BAD_COLOR
		else:
			indoor_humidity_label.color = OTHER_GOOD_COLOR

		in_press = data["indoor_pressure"]
		pstr = str(in_press) + "mb"
		if(pressure_label.text != pstr):
			pressure_label.text = pstr
		if in_press >= 1019 or in_press <= 1009:
			pressure_label.color = OTHER_BAD_COLOR
		else:
			pressure_label.color = OTHER_GOOD_COLOR

		up = data['uptime']
		uphours = up / 3600.0
		if uphours > 99:
			upstr = "99+"
		else:
			upstr = "{:.1f}".format(uphours)

		uptime_label.text = upstr

		mem_label.text = str(gc.mem_free())

	except Exception as e:
		print ("**** Exception updating other_weather:", e)
