# cookie labels

import displayio
import gc
import time
from adafruit_display_text import label

cookie_label = None

cookie_group = None

COOKIE_COLOR = (220, 80, 220)

def setup(box_x, box_y, font):
	global cookie_label

	global cookie_group

	cookie_label = label.Label(font, text="", color=COOKIE_COLOR, x=4, y=0)

	cookie_group = displayio.Group(x=box_x, y=box_y)

	cookie_group.append(cookie_label)

	return cookie_group

def update(data):
	global cookie_label

	try:
		cstr = data['cookie']
		if(cookie_label.text != cstr):
			# troubles with heap fragmentation force this
			cookie_label.text = ""
			gc.collect()
			time.sleep(0.5)
			cookie_label.text = cstr   # requires a 2-3K contiguous block
	except Exception as e:
		print ("**** Exception updating cookie:", e, cstr)
