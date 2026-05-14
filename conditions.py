# labels that display outside conditions

import displayio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.line import Line

temp_label = None
hum_label = None
cond_label = None

conditions_group = None

CONDITION_COLOR = (180,180,230)
LINE_COLOR = 0x404040

# temp colors
FREEZING_COLOR = (180,160,240)
COLD_COLOR = (100, 100, 200)
MILD_COLOR = (100, 200, 100)
WARM_COLOR = (200, 200, 100)
HOT_COLOR = (240, 100, 100)
SCORTCH_COLOR = (240, 140, 200)

# humidity colors
HUM_GOOD_COLOR = (40,240,40)
HUM_HI_COLOR = (220,240,20)
HUM_LO_COLOR = (220,240,20)

def setup(box_x, box_y, md_font, lg_font):
	global temp_label
	global hum_label
	global cond_label

	global conditions_group

	# temperature
	temp_label = label.Label(lg_font, text="", color=CONDITION_COLOR, x=2, y=22)
	temp_label.base_alignment = True

	# humidity
	hum_label = label.Label(md_font, text="", color=CONDITION_COLOR, x=128, y=39)
	hum_label.base_alignment = True

	# conditions
	cond_label = label.Label(md_font, text="Waiting for data...", color=CONDITION_COLOR, x=202, y=39)
	cond_label.base_alignment = True

	conditions_group = displayio.Group(x=box_x, y=box_y)
	conditions_group.append(temp_label)
	conditions_group.append(hum_label)
	conditions_group.append(cond_label)

	# dividing line
	conditions_group.append(Line(2, 62, 478, 62, LINE_COLOR))

	return conditions_group

def update(data):
	global temp_label
	global hum_label
	global cond_label

	try:
		tval = data['temp']
		tstr = str(tval)
		if(temp_label.text != tstr):
			temp_label.color = get_temp_color(tval)
			temp_label.text = str(tstr)

		# humidity
		hum = data['humidity']
		hstr = str(hum) + "%"
		if(hum_label.text != hstr):
			hum_label.color = get_humidity_color(hum)
			hum_label.text = hstr

		# conditions
		cstr = data['conditions']
		if(cond_label.text != cstr):
			cond_label.text = cstr
	except Exception as e:
		print ("**** Exception updating conditions:", e)

##### return the color associated with the temperature
def get_temp_color(t):
	c = CONDITION_COLOR

	try:
		t = int(t)
		if t > 100:
			c = SCORTCH_COLOR
		elif t > 89:
			c = HOT_COLOR
		elif t > 74:
			c = WARM_COLOR
		elif t > 49:
			c = MILD_COLOR
		elif t > 32:
			c = COLD_COLOR
		else:
			c = FREEZING_COLOR
	except Exception:
		print ("**** Exception getting temperature color:", e)

	return c;

##### return the color for a humidity
def get_humidity_color(hum):
	hum_color = HUM_GOOD_COLOR

	if hum<30:
		hum_color = HUM_LO_COLOR
	elif hum>80:
		hum_color = HUM_HI_COLOR

	return hum_color;

