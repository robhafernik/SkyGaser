# this module holds stuff ralated to displayintg Air Quality

import displayio

from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_text import label

# air quality colors
AQI_GOOD_COLOR = (40,240,40)
AQI_FAIR_COLOR = (140,240,20)
AQI_MODERATE_COLOR = (250,250,10)
AQI_BAD_COLOR = (240,120,120)
AQI_HORRIBLE_COLOR = (240,40,240)

aqi_rect_1 = None
aqi_rect_2 = None
aqi_rect_3 = None

aqi_label = None

aqi_group = None

##### setup air quality index display
def setup(box_x, box_y, font):
	global aqi_rect_1
	global aqi_rect_2
	global aqi_rect_3
	''
	global aqi_label
	global aqi_group

	aqi_rect_1 = RoundRect(x=2, y=1, width=90, height=60, r=10, outline=AQI_GOOD_COLOR)
	aqi_rect_2 = RoundRect(x=3, y=2, width=88, height=58, r=10, outline=AQI_GOOD_COLOR)
	aqi_rect_3 = RoundRect(x=4, y=3, width=86, height=56, r=10, outline=AQI_GOOD_COLOR)

	aqi_label = label.Label(font, text="AIR", color=AQI_GOOD_COLOR)
	aqi_label.anchor_point = (0.5, 0.0)
	aqi_label.anchored_position = (44, 22)

	aqi_group = displayio.Group(x=box_x, y=box_y)

	aqi_group.append(aqi_rect_1)
	aqi_group.append(aqi_rect_2)
	aqi_group.append(aqi_rect_3)
	aqi_group.append(aqi_label)

	return aqi_group

##### update display with AQI color
def update(data):
	global aqi_rect_1
	global aqi_rect_2
	global aqi_rect_3

	aqi_color = AQI_GOOD_COLOR
	culprit = "AIR"

	try:
		index = int(data['aqi_index'])

		if index == 1:
			aqi_color = AQI_GOOD_COLOR
		elif index == 2:
			aqi_color = AQI_FAIR_COLOR
		elif index == 3:
			aqi_color = AQI_MODERATE_COLOR
		elif index == 4:
			aqi_color = AQI_BAD_COLOR
		else:
			aqi_color = AQI_HORRIBLE_COLOR
	
		aqi_rect_1.outline = aqi_color
		aqi_rect_2.outline = aqi_color
		aqi_rect_3.outline = aqi_color

		co = data['aqi_co']
		if co == None: 
			co = 0
		no = data['aqi_no']
		if no == None: 
			no = 0
		no2 = data['aqi_no2']
		if no2 == None: 
			no2 = 0
		o3 = data['aqi_o3']
		if o3 == None: 
			o3 = 0
		so2 = data['aqi_so2']
		if so2 == None: 
			so2 = 0
		pm2_5 = data['aqi_pm2_5']
		if pm2_5 == None: 
			pm2_5 = 0
		pm_10 = data['aqi_pm10']
		if pm_10 == None: 
			pm_10 = 0
		nh3 = data['aqi_nh3']
		if nh3 == None: 
			nh3 = 0
	
		# if air quality index is a 1, then nothing's really bad
		culprit = "AIR"

		# else find the culprit
		if index > 1:
			culprit = get_air_quality_culprit (co,no,no2,o3,so2,pm2_5,pm_10,nh3)

	except Exception as e:
		print ("**** Exception updateing air_quality:", e, i)

	aqi_label.color = aqi_color
	if aqi_label.text != culprit:
		aqi_label.text = culprit

# get the worst air quality culprit by normalizing to "very bad" value for each pollutant
#    co and nh3 are not used in calculation
# 
# See this URL for API details and thresholds for "bad" levels: https://openweathermap.org/api/air-pollution
def get_air_quality_culprit(co,no,no2,o3,so2,pm2_5,pm10,nh3):
	top_score = 0.0
	culprit = "AIR"

	so2_score = so2 / 350  # magic number from above URL
	if so2_score > top_score:
		top_score = so2_score
		culprit = "SO2"

	no2_score = no2 / 200
	if no2_score > top_score:
		top_score = no2_score
		culprit = "NO2"

	pm10_score = pm10 / 200
	if pm10_score > top_score:
		top_score = pm10_score
		culprit = "P10"

	pm2_5_score = pm2_5 / 75
	if pm2_5_score > top_score:
		top_score = pm2_5_score
		culprit = "P2.5"

	o3_score = o3 / 180
	if o3_score > top_score:
		top_score = o3_score
		culprit = "O3"

	co_score = co / 15400
	if co_score > top_score:
		top_score = co_score
		culprit = "CO"

	return culprit






