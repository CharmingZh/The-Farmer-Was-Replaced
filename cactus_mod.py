# 仙人掌：相位化 Shear Sort（行/列交替 + 偶奇对齐）+ 连收触发

cx0 = 0
cx1 = 0
cy0 = 0
cy1 = 0
phase = 0          # 0 行相位；1 列相位
last_swaps = 1
swaps_now = 0

def set_region(x0, x1, y0, y1):
	global cx0
	global cx1
	global cy0
	global cy1
	cx0 = x0
	cx1 = x1
	cy0 = y0
	cy1 = y1

def in_region(x, y):
	return (x >= cx0) and (x <= cx1) and (y >= cy0) and (y <= cy1)

def reset_round():
	global swaps_now
	swaps_now = 0

def finish_round():
	global phase
	global last_swaps
	global swaps_now
	stable_two = (swaps_now == 0) and (last_swaps == 0)
	last_swaps = swaps_now
	phase = 1 - phase
	return stable_two

def process_cell(x, y):
	global swaps_now
	if not in_region(x, y):
		return
	s = measure()
	if s == None:
		return
	if phase == 0:
		# 行相位：偶格比 East，奇格比 West
		par = (x + y) % 2
		if par == 0:
			v = measure(East)
			if v != None:
				if v < s:
					swap(East)
					swaps_now = swaps_now + 1
		else:
			v2 = measure(West)
			if v2 != None:
				if v2 > s:
					swap(West)
					swaps_now = swaps_now + 1
	else:
		# 列相位：偶格比 North，奇格比 South
		par2 = (x + y) % 2
		if par2 == 0:
			v3 = measure(North)
			if v3 != None:
				if v3 < s:
					swap(North)
					swaps_now = swaps_now + 1
		else:
			v4 = measure(South)
			if v4 != None:
				if v4 > s:
					swap(South)
					swaps_now = swaps_now + 1

def maybe_mass_harvest_sw():
	if get_entity_type() == Entities.Cactus:
		if can_harvest():
			harvest()
			