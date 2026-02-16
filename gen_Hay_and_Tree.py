# =================================================================
#  32 无人机协同刷草+树 · 全图分块 + 棋盘式间隔种植
#  - 全图被划为 ~31 个子块（主机再负责 1 块），最大化并行
#  - 规则：按全局坐标 (x+y)%2 交替：偶数=草，奇数=树（或相反亦可）
#  - 每格循环：可收割则收割；若类型不符则翻地+改种为目标类型
#  - 语法约束：逐行语句、单 return、封装≤1层、无推导/无 lambda/.get()
# =================================================================

# ------------------ 基础移动与遍历 ------------------

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

# ------------------ 刷草+树（棋盘式）工人 ------------------

def target_entity_for(x, y):
	par = (x + y) % 2
	if par == 0:
		return Entities.Grass
	return Entities.Tree

def grass_tree_worker(x0, y0, x1, y1):
	quick_print("GT_BLOCK", x0, y0, x1, y1, "", "", "")
	path = rect_snake_iter(x0, y0, x1, y1)
	while True:
		i = 0
		while i < len(path):
			pos = path[i]
			tx = pos[0]
			ty = pos[1]
			move_to(tx, ty)
			want = target_entity_for(tx, ty)
			if can_harvest():
				harvest()
			if get_entity_type() != want:
				if get_ground_type() != Grounds.Soil:
					till()
				plant(want)
			i = i + 1

# ------------------ 分块规划（~31 个子块 + 1 主机） ------------------

def add_block(blocks, x0, y0, x1, y1):
	if x0 < 0:
		return None
	if y0 < 0:
		return None
	if x1 < x0:
		return None
	if y1 < y0:
		return None
	blocks.append((x0, y0, x1, y1))
	return None

def initial_column_strips(need, n):
	cols = need
	if cols > n:
		cols = n
	if cols < 1:
		cols = 1
	base = n // cols
	rem = n % cols
	blocks = []
	x_start = 0
	c = 0
	while c < cols:
		w = base
		if rem > 0:
			w = w + 1
			rem = rem - 1
		if w < 1:
			w = 1
		x0 = x_start
		x1 = x_start + w - 1
		if x1 >= n:
			x1 = n - 1
		add_block(blocks, x0, 0, x1, n - 1)
		x_start = x1 + 1
		c = c + 1
	return blocks

def split_block_h(block):
	x0 = block[0]
	y0 = block[1]
	x1 = block[2]
	y1 = block[3]
	h = y1 - y0 + 1
	if h <= 1:
		return (None, None)
	mid = y0 + (h // 2) - 1
	if mid < y0:
		mid = y0
	top = (x0, y0, x1, mid)
	bot = (x0, mid + 1, x1, y1)
	if top[3] < top[1]:
		top = None
	if bot[3] < bot[1]:
		bot = None
	return (top, bot)

def plan_gt_blocks(need):
	n = get_world_size()
	if n <= 0:
		return []
	blocks = initial_column_strips(need, n)
	idx = 0
	while len(blocks) < need and idx < len(blocks):
		b = blocks[idx]
		t, u = split_block_h(b)
		if t != None and u != None:
			blocks[idx] = t
			blocks.append(u)
		idx = idx + 1
	passes = 0
	while len(blocks) < need and passes < 6:
		i = 0
		changed = 0
		cur = len(blocks)
		while i < cur and len(blocks) < need:
			tb, bb = split_block_h(blocks[i])
			if tb != None and bb != None:
				blocks[i] = tb
				blocks.append(bb)
				changed = changed + 1
			i = i + 1
		if changed == 0:
			break
		passes = passes + 1
	while len(blocks) > need:
		blocks.pop()
	return blocks

# ------------------ 无人机封装 ------------------

def spawn_gt_block(a, b, c, d):
	def task():
		return grass_tree_worker(a, b, c, d)
	return spawn_drone(task)

# ------------------ 主程序 ------------------

def main():
	set_execution_speed(0)
	want = 32
	total_slots = max_drones()
	free = total_slots - num_drones()
	need = want - 1
	if need < 0:
		need = 0
	if free < need:
		need = free
	blocks = plan_gt_blocks(need + 1)
	quick_print("DRONES_PLANNED", need, "MAX", need, "SLOTS", free, "", "")
	i = 0
	while i < need:
		b = blocks[i]
		quick_print("DRONE", i + 1, "GT_BLOCK", "FROM", b[0], b[1], "TO", b[2], b[3])
		i = i + 1
	dispatched = 0
	j = 0
	while j < need:
		bb = blocks[j]
		ok = spawn_gt_block(bb[0], bb[1], bb[2], bb[3])
		if ok:
			dispatched = dispatched + 1
		j = j + 1
	quick_print("DRONES_DISPATCHED", dispatched, "OF", need, "", "", "", "")
	if len(blocks) >= need + 1:
		gb = blocks[need]
	else:
		if len(blocks) > 0:
			gb = blocks[0]
		else:
			n = get_world_size()
			gb = (0, 0, n - 1, n - 1)
	quick_print("MAIN_TAKES", gb[0], gb[1], gb[2], gb[3], "", "", "")
	grass_tree_worker(gb[0], gb[1], gb[2], gb[3])

main()
