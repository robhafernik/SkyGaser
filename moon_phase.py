# this module holds stuff ralated to displayintg phases of the moon

import displayio

import adafruit_imageload

m_new_grid = None
m_wax_crescent_grid = None
m_first_quarter_half_grid = None
m_wax_gibbos_grid = None
m_full_grid = None
m_wan_gibbos_grid = None
m_last_quarter_half_grid = None
m_wan_crescent_grid = None

last_grid = None

moon_group = None

##### set up moon phase bitmaps (aobut 5K of RAM)
def setup(box_x, box_y):
	global m_new_grid
	global m_wax_crescent_grid
	global m_first_quarter_half_grid
	global m_wax_gibbos_grid
	global m_full_grid
	global m_wan_gibbos_grid
	global m_last_quarter_half_grid
	global m_wan_crescent_grid

	global moon_group

	# load the moon graphics into memory (about 5K), but don't show them
	m_new, palette = adafruit_imageload.load("/moon/new.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_new_grid = displayio.TileGrid(m_new, pixel_shader=palette, x=2, y=0)

	m_wax_crescent, palette = adafruit_imageload.load("/moon/wax_crescent.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_wax_crescent_grid = displayio.TileGrid(m_wax_crescent, pixel_shader=palette, x=2, y=0)

	m_first_quarter_half, palette = adafruit_imageload.load("/moon/first_quarter_half.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_first_quarter_half_grid = displayio.TileGrid(m_first_quarter_half, pixel_shader=palette, x=2, y=0)

	m_wax_gibbos, palette = adafruit_imageload.load("/moon/wax_gibbos.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_wax_gibbos_grid = displayio.TileGrid(m_wax_gibbos, pixel_shader=palette, x=2, y=0)

	m_full, palette = adafruit_imageload.load("/moon/full.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_full_grid = displayio.TileGrid(m_full, pixel_shader=palette, x=2, y=0)

	m_wan_gibbos, palette = adafruit_imageload.load("/moon/wan_gibbos.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_wan_gibbos_grid = displayio.TileGrid(m_wan_gibbos, pixel_shader=palette, x=2, y=0)

	m_last_quarter_half, palette = adafruit_imageload.load("/moon/last_quarter_half.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_last_quarter_half_grid = displayio.TileGrid(m_last_quarter_half, pixel_shader=palette, x=2, y=0)

	m_wan_crescent, palette = adafruit_imageload.load("/moon/wan_crescent.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
	m_wan_crescent_grid = displayio.TileGrid(m_wan_crescent, pixel_shader=palette, x=2, y=0)

	moon_group = displayio.Group(x=box_x, y=box_y)

	return moon_group

##### update moon phose bitmap
def update(data):
	try:
		global last_grid
		
		fase = data['moon_phase']

		grid = m_new_grid
		
		if fase >= 0.9375 or fase <= 0.0625:
			grid = m_new_grid
		elif fase > 0.8125:
			grid = m_wan_crescent_grid
		elif fase > 0.6825:
			grid = m_last_quarter_half_grid
		elif fase > 0.5625:
			grid = m_wan_gibbos_grid
		elif fase > 0.4375:
			grid = m_full_grid
		elif fase > 0.3125:
			grid = m_wax_gibbos_grid
		elif fase > 0.1875:
			grid = m_first_quarter_half_grid
		elif fase > 0.0625:
			grid = m_wax_crescent_grid

		if grid != last_grid:
			
			# remove last moon
			try:
				if last_grid != None:
					moon_group.remove(last_grid)
			except Exception as ee:
				print ("**** Exception removing last_grid:", ee, last_grid, moon_group)

			# draw the current moon
			if grid != None:
				moon_group.append(grid)
				last_grid = grid

	except Exception as e:
		print ("**** Exception updating moon_phase:", e, last_grid, grid, fase)

