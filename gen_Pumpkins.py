# =================================================================
#  智能 32 无人机协同农场 v4.0（定尺32×32 · 地块吃满 · 向日葵全收集）
#  - 右侧两列：草/树交替（棋盘式）
#  - 向日葵：顶部两行，一行一机，逐格全收集
#  - 胡萝卜：底部两行，一行一机
#  - 南瓜：中央 30×28 区切成 13 条竖带，每带 2 机（队长+行工），主机接最后一带
#  - 语法约束：无三元、无推导、单 return、封装≤1层、无 lambda/.get()
# =================================================================

# ------------------ 基础移动 ------------------

def move_to(tx, ty):
	px = get_pos_x()
	py = get_pos_y()
	while px < tx:
		move(East)
		px = px + 1
	while px > tx:
		move(West)
		px = px - 1
	while py < ty:
		move(North)
		py = py + 1
	while py > ty:
		move(South)
		py = py - 1

def rect_snake_iter(x0, y0, x1, y1):
	path = []
	y = y0
	while y <= y1:
		if (y - y0) % 2 == 0:
			x = x0
			while x <= x1:
				path.append((x, y))
				x = x + 1
		else:
			x = x1
			while x >= x0:
				path.append((x, y))
				x = x - 1
		y = y + 1
	return path

def ensure_plant(plant_type):
	if get_ground_type() != Grounds.Soil:
		till()
	if get_entity_type() != plant_type:
		plant(plant_type)

# ------------------ 南瓜逻辑 ------------------

def maintain_pumpkin_block(x0, y0, x1, y1):
	path = rect_snake_iter(x0, y0, x1, y1)
	i = 0
	while i < len(path):
		pos = path[i]
		move_to(pos[0], pos[1])
		if get_entity_type() != Entities.Pumpkin:
			if get_ground_type() != Grounds.Soil:
				till()
			plant(Entities.Pumpkin)
		i = i + 1

def maintain_pumpkin_rows(x0, y0, x1, y1, row_from_abs, row_to_abs):
	ry = row_from_abs
	while ry <= row_to_abs:
		x = x0
		if (ry - y0) % 2 != 0:
			x = x1
		if (ry - y0) % 2 == 0:
			while x <= x1:
				move_to(x, ry)
				if get_entity_type() != Entities.Pumpkin:
					if get_ground_type() != Grounds.Soil:
						till()
					plant(Entities.Pumpkin)
				x = x + 1
		else:
			while x >= x0:
				move_to(x, ry)
				if get_entity_type() != Entities.Pumpkin:
					if get_ground_type() != Grounds.Soil:
						till()
					plant(Entities.Pumpkin)
				x = x - 1
		ry = ry + 1

def block_all_pumpkins(x0, y0, x1, y1):
	def pred():
		return get_entity_type() == Entities.Pumpkin
	return area_all(pred, x0, y0, x1, y1)

def block_all_harvestable(x0, y0, x1, y1):
	def pred():
		if get_entity_type() != Entities.Pumpkin:
			return False
		return can_harvest()
	return area_all(pred, x0, y0, x1, y1)

def area_all(predicate_fn, x0, y0, x1, y1):
	path = rect_snake_iter(x0, y0, x1, y1)
	i = 0
	while i < len(path):
		pos = path[i]
		move_to(pos[0], pos[1])
		if not predicate_fn():
			return False
		i = i + 1
	return True

def harvest_giant_if_ready(x0, y0, x1, y1):
	all_p = block_all_pumpkins(x0, y0, x1, y1)
	if not all_p:
		return False
	all_rdy = block_all_harvestable(x0, y0, x1, y1)
	if not all_rdy:
		return False
	cx = (x0 + x1) // 2
	cy = (y0 + y1) // 2
	move_to(cx, cy)
	if can_harvest():
		harvest()
		quick_print("GIANT_OK", x0, y0, x1, y1, "", "", "")
		return True
	return False

def pumpkin_worker(x0, y0, x1, y1):
	quick_print("P_CAPTAIN", x0, y0, x1, y1, "", "", "")
	while True:
		maintain_pumpkin_block(x0, y0, x1, y1)
		ok = harvest_giant_if_ready(x0, y0, x1, y1)
		if ok:
			maintain_pumpkin_block(x0, y0, x1, y1)

def pumpkin_row_worker(x0, y0, x1, y1, row_from_abs, row_to_abs):
	quick_print("P_ROWS", row_from_abs, row_to_abs, x0, y0, x1, y1, "")
	while True:
		maintain_pumpkin_rows(x0, y0, x1, y1, row_from_abs, row_to_abs)

# ------------------ 胡萝卜 / 向日葵 / 草木交替 ------------------

def snake_band_worker(x0, y0, x1, y1, plant_type):
	quick_print("BAND", plant_type, x0, y0, x1, y1, "", "")
	path = rect_snake_iter(x0, y0, x1, y1)
	while True:
		j = 0
		while j < len(path):
			pos = path[j]
			move_to(pos[0], pos[1])
			if can_harvest():
				harvest()
			if get_entity_type() != plant_type:
				if get_ground_type() != Grounds.Soil:
					till()
				plant(plant_type)
			j = j + 1

def grass_tree_band_worker(x0, y0, x1, y1):
	quick_print("GRASS_TREE_BAND", x0, y0, x1, y1, "", "", "")
	path = rect_snake_iter(x0, y0, x1, y1)
	while True:
		i = 0
		while i < len(path):
			pos = path[i]
			tx = pos[0]
			ty = pos[1]
			move_to(tx, ty)
			if can_harvest():
				harvest()
			par = (tx + ty) % 2
			if par == 0:
				if get_entity_type() != Entities.Grass:
					if get_ground_type() != Grounds.Soil:
						till()
					plant(Entities.Grass)
			else:
				if get_entity_type() != Entities.Tree:
					if get_ground_type() != Grounds.Soil:
						till()
					plant(Entities.Tree)
			i = i + 1

def sunflower_row_worker(x0, y_abs, x1):
	quick_print("SUN_ROW", y_abs, x0, x1, "", "", "", "")
	# 初始化整行
	x = x0
	while x <= x1:
		move_to(x, y_abs)
		if get_ground_type() != Grounds.Soil:
			till()
		if get_entity_type() != Entities.Sunflower:
			plant(Entities.Sunflower)
		x = x + 1
	# 维护：不筛选最大花瓣，逐格全收集
	while True:
		x2 = x0
		while x2 <= x1:
			move_to(x2, y_abs)
			if can_harvest():
				harvest()
			if get_entity_type() != Entities.Sunflower:
				if get_ground_type() != Grounds.Soil:
					till()
				plant(Entities.Sunflower)
			x2 = x2 + 1

def carrot_row_worker(x0, y_abs, x1):
	quick_print("CARROT_ROW", y_abs, x0, x1, "", "", "", "")
	x = x0
	while x <= x1:
		move_to(x, y_abs)
		if get_ground_type() != Grounds.Soil:
			till()
		if get_entity_type() != Entities.Carrot:
			plant(Entities.Carrot)
		x = x + 1
	while True:
		x2 = x0
		while x2 <= x1:
			move_to(x2, y_abs)
			if can_harvest():
				harvest()
			if get_entity_type() != Entities.Carrot:
				if get_ground_type() != Grounds.Soil:
					till()
				plant(Entities.Carrot)
			x2 = x2 + 1

# ------------------ 布局与条带切分（精准吃满 32×32） ------------------

def plan_layout_fixed_32():
	# 固定地图为 32×32
	n = 32
	# 顶部向日葵 2 行、底部胡萝卜 2 行
	sb = 2
	cb = 2
	# 右侧两列草/树
	grass_tree_band = (n - 2, 0, n - 1, n - 1)
	# 向日葵条带（两行）
	sun_band = (0, n - sb, n - 3, n - 1)
	# 胡萝卜条带（两行）
	carrot_band = (0, 0, n - 3, cb - 1)
	# 中央南瓜可用域：x 0..29，y 2..29
	crop_x0 = 0
	crop_x1 = n - 3
	crop_y0 = cb
	crop_y1 = n - 1 - sb
	return (carrot_band, sun_band, grass_tree_band, crop_x0, crop_y0, crop_x1, crop_y1)

def plan_pumpkin_strips(x0, y0, x1, y1, k):
	# 把矩形 [x0..x1]×[y0..y1] 精确切成 k 条竖向条带（宽度差最多 1）
	blocks = []
	W = x1 - x0 + 1
	H = y1 - y0 + 1
	if k < 1:
		return blocks
	base = W // k
	rem = W % k
	start = x0
	i = 0
	while i < k:
		w = base
		if rem > 0:
			w = w + 1
			rem = rem - 1
		xs = start
		xe = start + w - 1
		if xe > x1:
			xe = x1
		if xs <= xe:
			blocks.append((xs, y0, xe, y1))
		start = xe + 1
		i = i + 1
	return blocks

# ------------------ 无人机封装 ------------------

def spawn_block(fn, a, b, c, d):
	def task():
		return fn(a, b, c, d)
	return spawn_drone(task)

def spawn_pumpkin_rows(a, b, c, d, rf_abs, rt_abs):
	def task():
		return pumpkin_row_worker(a, b, c, d, rf_abs, rt_abs)
	return spawn_drone(task)

def spawn_carrot_row(x0, y_abs, x1):
	def task():
		return carrot_row_worker(x0, y_abs, x1)
	return spawn_drone(task)

def spawn_sun_row(x0, y_abs, x1):
	def task():
		return sunflower_row_worker(x0, y_abs, x1)
	return spawn_drone(task)

def spawn_grass_tree_band(a, b, c, d):
	def task():
		return grass_tree_band_worker(a, b, c, d)
	return spawn_drone(task)

# ------------------ 主程序（打印计划与分工） ------------------

def main():
	set_execution_speed(0)
	carrot_band, sun_band, grass_tree_band, px0, py0, px1, py1 = plan_layout_fixed_32()
	total_slots = max_drones()
	want = 32
	free = total_slots - num_drones()
	need = want - 1
	if need < 0:
		need = 0
	if free < need:
		need = free

	# 先分配功能带：向日葵(2) + 草树(1) + 胡萝卜(2) 共 5
	assign = []
	used = 0
	if sun_band != None:
		y = sun_band[1]
		while y <= sun_band[3] and used < need:
			assign.append(("SUN_ROW", sun_band[0], y, sun_band[2], y))
			used = used + 1
			y = y + 1
	if grass_tree_band != None:
		if used < need:
			assign.append(("GRASS_TREE_BAND", grass_tree_band[0], grass_tree_band[1], grass_tree_band[2], grass_tree_band[3]))
			used = used + 1
	if carrot_band != None:
		y2 = carrot_band[1]
		while y2 <= carrot_band[3] and used < need:
			assign.append(("CARROT_ROW", carrot_band[0], y2, carrot_band[2], y2))
			used = used + 1
			y2 = y2 + 1

	# 计算南瓜条带数量（每带 2 机：队长+行工）
	remain = need - used
	if remain < 0:
		remain = 0
	pumpkin_blocks = remain // 2
	if pumpkin_blocks < 1:
		pumpkin_blocks = 1

	blocks = plan_pumpkin_strips(px0, py0, px1, py1, pumpkin_blocks)

	# 为每条带安排：1 队长 + 1 行工（行工负责下半区）
	i = 0
	while i < len(blocks) and used + 2 <= need:
		b = blocks[i]
		assign.append(("P_CAPTAIN", b[0], b[1], b[2], b[3]))
		used = used + 1
		h = b[3] - b[1] + 1
		half = h // 2
		if half < 1:
			half = 1
		rf_abs = b[1]
		rt_abs = b[1] + half - 1
		if rt_abs > b[3]:
			rt_abs = b[3]
		assign.append(("P_ROWS", b[0], rf_abs, b[2], rt_abs))
		used = used + 1
		i = i + 1

	# 打印计划
	quick_print("DRONES_PLANNED", len(assign), "MAX", need, "SLOTS", free, "", "")
	idx = 0
	while idx < len(assign):
		it = assign[idx]
		quick_print("DRONE", idx + 1, it[0], "FROM", it[1], it[2], "TO", it[3], it[4])
		idx = idx + 1

	# 派发
	dispatched = 0
	k = 0
	while k < len(assign) and dispatched < need:
		item = assign[k]
		if item[0] == "SUN_ROW":
			ok = spawn_sun_row(item[1], item[2], item[3])
			if ok:
				dispatched = dispatched + 1
		elif item[0] == "GRASS_TREE_BAND":
			ok = spawn_grass_tree_band(item[1], item[2], item[3], item[4])
			if ok:
				dispatched = dispatched + 1
		elif item[0] == "CARROT_ROW":
			ok = spawn_carrot_row(item[1], item[2], item[3])
			if ok:
				dispatched = dispatched + 1
		elif item[0] == "P_CAPTAIN":
			ok = spawn_block(pumpkin_worker, item[1], item[2], item[3], item[4])
			if ok:
				dispatched = dispatched + 1
		elif item[0] == "P_ROWS":
			ok = spawn_pumpkin_rows(item[1], item[2], item[3], item[4], item[2], item[4])
			if ok:
				dispatched = dispatched + 1
		k = k + 1
	quick_print("DRONES_DISPATCHED", dispatched, "OF", need, "", "", "", "")

	# 主机接最后一条南瓜带（若未生成则接第一条）
	if len(blocks) > 0:
		bm = blocks[len(blocks) - 1]
		quick_print("MAIN_TAKES", bm[0], bm[1], bm[2], bm[3], "", "", "")
		pumpkin_worker(bm[0], bm[1], bm[2], bm[3])
	else:
		# 兜底：全图
		quick_print("MAIN_TAKES_FALLBACK", 0, 0, 31, 31, "", "", "")
		pumpkin_worker(0, 0, 31, 31)

main()
