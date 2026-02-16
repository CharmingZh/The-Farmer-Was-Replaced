# =================================================================
#  32线程刷Power（向日葵能量）· 全图边种边采 v2.1（环面移动优化）
#  - 移动采用环面最短路：越界一步即瞬移到另一侧（上到下、左到右）
#  - 32 个工人均分行段；各自蛇形循环：能收就收，非葵就翻地补种
#  - 语法友好：无三元/推导/is/lambda/.get()
# =================================================================

# ---------------- 基础工具（环面移动） ----------------

def move_to(tx, ty):
	n = get_world_size()
	px = get_pos_x()
	py = get_pos_y()

	# ---- X 方向：选更短的环面距离 ----
	dx_fwd = (tx - px) % n
	dx_back = (px - tx) % n
	if dx_fwd <= dx_back:
		i = 0
		while i < dx_fwd:
			move(East)
			i = i + 1
	else:
		i = 0
		while i < dx_back:
			move(West)
			i = i + 1

	# 更新当前位置（可选；不依赖也能正确，因为下方用环面差）
	px = get_pos_x()
	py = get_pos_y()

	# ---- Y 方向：选更短的环面距离 ----
	dy_fwd = (ty - py) % n
	dy_back = (py - ty) % n
	if dy_fwd <= dy_back:
		j = 0
		while j < dy_fwd:
			move(North)
			j = j + 1
	else:
		j = 0
		while j < dy_back:
			move(South)
			j = j + 1

def ensure_sunflower_here():
	if get_ground_type() != Grounds.Soil:
		till()
	if get_entity_type() != Entities.Sunflower:
		plant(Entities.Sunflower)

def rect_snake_iter_row(x0, x1, y):
	path = []
	if (y % 2) == 0:
		x = x0
		while x <= x1:
			path.append((x, y))
			x = x + 1
	else:
		x = x1
		while x >= x0:
			path.append((x, y))
			x = x - 1
	return path

# ---------------- 工人：负责一个连续行区间 ----------------

def sunflower_strip_worker(y_from, y_to, x0, x1):
	quick_print("SUN_STRIP", y_from, y_to, x0, x1, "", "", "")
	# 首次通扫：填满该区间
	y = y_from
	while y <= y_to:
		row = rect_snake_iter_row(x0, x1, y)
		i = 0
		while i < len(row):
			pos = row[i]
			move_to(pos[0], pos[1])
			if can_harvest():
				harvest()
			ensure_sunflower_here()
			i = i + 1
		y = y + 1
	# 持续循环：边种边采（幂等）
	while True:
		yy = y_from
		while yy <= y_to:
			row2 = rect_snake_iter_row(x0, x1, yy)
			j = 0
			while j < len(row2):
				p = row2[j]
				move_to(p[0], p[1])
				# harvest()
				if can_harvest():
					harvest()
				if get_entity_type() != Entities.Sunflower:
					if get_ground_type() != Grounds.Soil:
						till()
					plant(Entities.Sunflower)
				j = j + 1
			yy = yy + 1

# ---------------- 生成子机 ----------------

def spawn_strip_worker(y_from, y_to, x0, x1):
	def task():
		return sunflower_strip_worker(y_from, y_to, x0, x1)
	return spawn_drone(task)

# ---------------- 主程序 ----------------

def main():
	set_execution_speed(0)
	n = get_world_size()
	x0 = 0
	x1 = n - 1
	y0 = 0
	y1 = n - 1

	# 规划线程数量（最多32；含主线程）
	total_slots = max_drones()
	already = num_drones()
	want = 32
	if want > total_slots:
		want = total_slots
	workers_total = want
	if workers_total < 1:
		workers_total = 1

	# 将 n 行均分为 workers_total 个连续区间（前 rem 个多 1 行）
	base = n // workers_total
	rem = n - base * workers_total

	assignments = []
	w = 0
	cur_y = 0
	while w < workers_total:
		size = base
		if rem > 0:
			size = size + 1
			rem = rem - 1
		y_from = cur_y
		y_to = cur_y + size - 1
		if y_to >= n:
			y_to = n - 1
		assignments.append((y_from, y_to))
		cur_y = y_to + 1
		w = w + 1

	# 打印计划
	quick_print("DRONES_PLANNED", workers_total, "WORLD", n, "X", x0, x1, "")
	i0 = 0
	while i0 < len(assignments):
		seg = assignments[i0]
		quick_print("DRONE_PLAN", i0 + 1, "YFROM", seg[0], "YTO", seg[1], "X", x0, x1)
		i0 = i0 + 1

	# 启动子机：前 workers_total-1 个由子机承担
	to_spawn = workers_total - 1
	spawned = 0
	i = 0
	while i < to_spawn:
		seg2 = assignments[i]
		ok = spawn_strip_worker(seg2[0], seg2[1], x0, x1)
		if ok:
			spawned = spawned + 1
			quick_print("SPAWNED", i + 1, seg2[0], seg2[1], "", "", "", "")
		i = i + 1
	quick_print("SPAWN_SUMMARY", spawned, "OF", to_spawn, "", "", "", "", "")

	# 主线程承担最后一个区间
	last = assignments[len(assignments) - 1]
	quick_print("MAIN_TAKE", last[0], last[1], x0, x1, "", "", "")
	sunflower_strip_worker(last[0], last[1], x0, x1)

main()