# labels that display weather alerts if any
# if no alerts are available, the forecast is shown

import displayio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.line import Line

alert_label_1 = None
alert_label_2 = None

alert_group = None

ALERT_COLOR = (240, 140, 200)
FORECAST_COLOR = (140, 140, 140)
BIRTHDAY_COLOR = (220, 180, 180)

def setup(box_x, box_y, font):
	global alert_label_1
	global alert_label_2
	global alert_group

	alert_label_1 = label.Label(font, text="", color=ALERT_COLOR, x=10, y=0)
	alert_label_1.base_alignment = True

	alert_label_2 = label.Label(font, text="", color=ALERT_COLOR, x=10, y=24)
	alert_label_2.base_alignment = True

	alert_group = displayio.Group(x=box_x,y=box_y)
	alert_group.append(alert_label_1)
	alert_group.append(alert_label_2)

	return alert_group

def update(data):
	try:
		if (data['day_of_month'] == 28) and (data['month'] == "May"):
			astr = "*** Happy Birthday Patricia ***"
			if(alert_label_1.text != astr):
				alert_label_1.color = BIRTHDAY_COLOR
				alert_label_1.text = astr

			if(alert_label_2.text != ""):
				alert_label_2.text = ""
		elif data['show_alerts'] == True:
			astr = data['weather_alert_1']
			if(alert_label_1.text != astr):
				alert_label_1.color = ALERT_COLOR
				alert_label_1.text = astr

			astr = data['weather_alert_2']
			if(alert_label_2.text != astr):
				alert_label_2.color = ALERT_COLOR
				alert_label_2.text = astr

		else: 
			astr = data['forecast_temps']
			if(alert_label_1.text != astr):
				alert_label_1.color = FORECAST_COLOR
				alert_label_1.text = astr

			astr = data['forecast_cond']
			if(alert_label_2.text != astr):
				alert_label_2.color = FORECAST_COLOR
				alert_label_2.text = astr

	except Exception as e:
		print ("**** Exception updating alerts:", e)
