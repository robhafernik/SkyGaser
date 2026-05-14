# date and time labels

import displayio
#from adafruit_display_text import bitmap_label
from adafruit_display_shapes.line import Line

from adafruit_display_text import label

date_label = None
time_label = None

date_time_group = None

TIME_COLOR = (220, 220, 240)
DATE_COLOR = (220, 220, 240)
TOP_LINE_COLOR = 0x404040
BOT_LINE_COLOR = 0x808080

def setup(box_x, box_y, md_font, lg_font):
	global date_label
	global time_label

	global date_time_group

	date_label = label.Label(md_font, text="", color=DATE_COLOR, x=4, y=42)

	time_label = label.Label(lg_font, text="", color=TIME_COLOR, base_alignment=True)
	time_label.anchor_point = (1.0, 0.0)
	time_label.anchored_position = (476, 5)

	date_time_group = displayio.Group(x=box_x, y=box_y)

	date_time_group.append(date_label)
	date_time_group.append(time_label)
	date_time_group.append(Line(2, 0, 478, 0, TOP_LINE_COLOR))
	date_time_group.append(Line(2, 62, 478, 62, BOT_LINE_COLOR))

	return date_time_group


def update(data):
    global date_label
    global time_label

    try:
        # Safe string conversion with defaults
        dow = str(data.get('day_of_week', '???'))
        mon = str(data.get('month', '???'))
        dom = str(data.get('day_of_month', '00'))
        hour = str(data.get('hour', '00'))
        minute = str(data.get('minute', '00'))   # force str

        dstr = dow + ", " + mon + " " + dom
        if date_label.text != dstr:
            date_label.text = dstr

        # Pad minute safely (now that it's str)
        mins = minute
        if len(minute) == 1:
            mins = "0" + minute
        # or simpler: mins = f"{int(minute):02d}" but this handles non-numeric better

        tstr = hour + ":" + mins
        if time_label.text != tstr:
            time_label.text = tstr

    except Exception as e:
        print("**** Exception updating date_time:", e)
        # Optional: set fallback display
        date_label.text = "Date Error"
        time_label.text = "??:??"