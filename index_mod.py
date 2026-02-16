# 全图二维索引：实体/地面/水/花瓣（避免同格重复调用/重复操作）

entity_map = []
ground_map = []
water_map  = []
petal_map  = []   # 仅向日葵格记录（其他置 -1）

def init_maps():
	n = get_world_size()
	global entity_map
	global ground_map
	global water_map
	global petal_map
	entity_map = []
	ground_map = []
	water_map  = []
	petal_map  = []
	for _ in range(n):
		row_e = []
		row_g = []
		row_w = []
		row_p = []
		for __ in range(n):
			row_e.append(None)
			row_g.append(None)
			row_w.append(-1.0)
			row_p.append(-1)
		entity_map.append(row_e)
		ground_map.append(row_g)
		water_map.append(row_w)
		petal_map.append(row_p)

def update_cell(x, y, is_sunflower_band):
	et = get_entity_type()
	gd = get_ground_type()
	wt = get_water()
	entity_map[y][x] = et
	ground_map[y][x] = gd
	water_map[y][x]  = wt
	if is_sunflower_band and et == Entities.Sunflower:
		p = measure()
		if p != None:
			petal_map[y][x] = p

def get_entity_cached(x, y):
	return entity_map[y][x]

def get_ground_cached(x, y):
	return ground_map[y][x]

def get_water_cached(x, y):
	return water_map[y][x]

def get_petal_cached(x, y):
	return petal_map[y][x]
	