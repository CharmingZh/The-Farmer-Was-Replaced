# =================================================================
#  32 线程专心刷奇异物质 · 全自动版 (Bush-only, Weird_Substance farm)
#  - 仅使用灌木 Bush
#  - 32 台无人机各守一个格子：原地种->施肥->收->复种->施肥
#  - 若缺干草，子机会自行去收割成熟草补料后返回
#  - 不再种/收任何其他作物（除了为成本而收草）
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

# ------------------ 资源辅助 ------------------

def find_harvestable_grass():
	# 全图蛇形扫描，找一株可收的草
	n = get_world_size()
	y = 0
	while y < n:
		x_start = 0
		x_end = n
		x_step = 1
		if (y % 2) != 0:
			x_start = n - 1
			x_end = -1
			x_step = -1
		x = x_start
		while x != x_end:
			move_to(x, y)
			if get_entity_type() == Entities.Grass and can_harvest():
				return (x, y)
			x = x + x_step
		y = y + 1
	return None

def ensure_bush_with_cost(home_x, home_y, bush_cost):
	# 确保在当前位置种成 Bush；若缺干草则去收草再回来
	if Items.Hay in bush_cost:
		need = bush_cost[Items.Hay]
		while num_items(Items.Hay) < need:
			quick_print("BUSH_NEED_HAY", "AT", home_x, home_y, "HAVE", num_items(Items.Hay), "NEED", need)
			curx = get_pos_x()
			cury = get_pos_y()
			pos = find_harvestable_grass()
			if pos != None:
				harvest()
				quick_print("BUSH_GET_HAY", pos[0], pos[1], "", "", "", "", "")
				move_to(curx, cury)
			else:
				# 没草可收，原地等待一点动作循环（不空转 CPU）
				k = 0
				while k < 200:
					k = k + 1
				# 再次检查一次，循环继续
	if get_ground_type() != Grounds.Soil:
		till()
	if get_entity_type() != Entities.Bush:
		plant(Entities.Bush)

# ------------------ Weird 物质刷法（单格原地循环） ------------------

def weird_tile_worker(wx, wy):
	# 每个子机固定在 (wx,wy) 原地刷：Bush -> 施肥 -> 收 -> 复种 -> 施肥
	quick_print("WEIRD_WORKER_START", wx, wy, "", "", "", "", "")
	move_to(wx, wy)
	bush_cost = get_cost(Entities.Bush)

	# 首次落地：若不是灌木就补种，并立刻施肥（感染+加速）
	if get_entity_type() != Entities.Bush:
		ensure_bush_with_cost(wx, wy, bush_cost)
		if num_items(Items.Fertilizer) > 0:
			use_item(Items.Fertilizer)

	while True:
		move_to(wx, wy)

		# 可收则收 -> 立刻复种 -> 施肥维持感染与加速
		if can_harvest():
			harvest()
			if get_ground_type() != Grounds.Soil:
				till()
			if get_entity_type() != Entities.Bush:
				ensure_bush_with_cost(wx, wy, bush_cost)
			if num_items(Items.Fertilizer) > 0:
				use_item(Items.Fertilizer)

		# 不可收时：若不是灌木，补种；若是灌木，尽量施肥催熟并保持感染
		else:
			if get_entity_type() != Entities.Bush:
				ensure_bush_with_cost(wx, wy, bush_cost)
				if num_items(Items.Fertilizer) > 0:
					use_item(Items.Fertilizer)
			else:
				if num_items(Items.Fertilizer) > 0:
					use_item(Items.Fertilizer)

		# 小延时，避免过度空转
		j = 0
		while j < 50:
			j = j + 1

# ------------------ 生成 32 个“岗位坐标” ------------------

def build_32_slots():
	# 在世界里均匀挑选 32 个不相邻过近的坐标，避免互相走位干扰
	# 策略：按 8x4 网格中心取点，自动裁剪到地图范围
	slots = []
	n = get_world_size()
	grid_w = 8
	grid_h = 4
	cell_x = n / grid_w
	cell_y = n / grid_h
	gy = 0
	while gy < grid_h:
		gx = 0
		while gx < grid_w:
			cx = (gx * cell_x) + (cell_x / 2)
			cy = (gy * cell_y) + (cell_y / 2)
			# 边界保护
			if cx < 0:
				cx = 0
			if cy < 0:
				cy = 0
			if cx > n - 1:
				cx = n - 1
			if cy > n - 1:
				cy = n - 1
			slots.append((cx, cy))
			gx = gx + 1
		gy = gy + 1
	# 若地图较小也至少返回 32 个以内
	return slots

# ------------------ 子机封装 ------------------

def spawn_weird_worker(ax, ay):
	def task():
		return weird_tile_worker(ax, ay)
	return spawn_drone(task)

# ------------------ 主程序 ------------------

def main():
	quick_print("WEIRD_FARM_32_START", "", "", "", "", "", "", "")
	set_execution_speed(0)

	slots = build_32_slots()
	total_slots = max_drones()
	free = total_slots - num_drones()
	want = 32
	# 你最多能再生出 need 台子机（主机自己也要占一个岗位）
	need = want - 1
	if need < 0:
		need = 0
	if free < need:
		need = free

	# 打印岗位
	quick_print("DRONES_PLANNED", want, "CAN_SPAWN", need, "ALREADY", num_drones(), "MAX", total_slots, "")
	i = 0
	while i < want:
		if i < len(slots):
			quick_print("SLOT", i + 1, "AT", slots[i][0], slots[i][1], "", "", "")
		i = i + 1

	# 先派出前 need 个子机
	spawned = 0
	k = 0
	while k < need and k < len(slots):
		ok = spawn_weird_worker(slots[k][0], slots[k][1])
		if ok:
			spawned = spawned + 1
		k = k + 1
	quick_print("DRONES_DISPATCHED", spawned, "OF", need, "", "", "", "")

	# 主机占用下一个岗位（或第 1 个）
	host_index = spawned
	if host_index >= len(slots):
		host_index = 0
	quick_print("HOST_TAKES_SLOT", host_index + 1, "AT", slots[host_index][0], slots[host_index][1], "", "", "")
	weird_tile_worker(slots[host_index][0], slots[host_index][1])

# --- 执行 ---
main()
