# =================================================================
#  32 无人机协同刷胡萝卜 · 全图分块 + 蛇形维护
#  - 自动把地图划分成 ~31 个子块（主机再负责 1 个），最大化并行度
#  - 每个无人机在自己子块中：可收割就收割；不是胡萝卜就翻地+补种
#  - 动态适配任意地图大小；确保不会生成空块
#  - 打印派工明细：每个无人机负责的矩形范围
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

# ------------------ 刷胡萝卜工人 ------------------

def carrot_worker(x0, y0, x1, y1):
	quick_print("CARROT_BLOCK", x0, y0, x1, y1, "", "", "")
	path = rect_snake_iter(x0, y0, x1, y1)
	while True:
		i = 0
		while i < len(path):
			pos = path[i]
			move_to(pos[0], pos[1])
			if can_harvest():
				harvest()
			if get_entity_type() != Entities.Carrot:
				if get_ground_type() != Grounds.Soil:
					till()
				plant(Entities.Carrot)
			i = i + 1

# ------------------ 分块规划（生成 ~31 个子块） ------------------

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

def plan_carrot_blocks(need):
	n = get_world_size()
	if n <= 0:
		return []
	# 第一步：纵向切条
	blocks = initial_column_strips(need, n)
	# 第二步：不够就横向二分
	idx = 0
	while len(blocks) < need and idx < len(blocks):
		b = blocks[idx]
		top, bot = split_block_h(b)
		if top != None and bot != None:
			blocks[idx] = top
			blocks.append(bot)
		idx = idx + 1
	# 第三步：必要时再多轮二分
	passes = 0
	while len(blocks) < need and passes < 5:
		i = 0
		changed = 0
		cur_len = len(blocks)
		while i < cur_len and len(blocks) < need:
			tb, bb = split_block_h(blocks[i])
			if tb != None and bb != None:
				blocks[i] = tb
				blocks.append(bb)
				changed = changed + 1
			i = i + 1
		if changed == 0:
			break
		passes = passes + 1
	# 过多就截断
	while len(blocks) > need:
		blocks.pop()
	return blocks

# ------------------ 无人机封装 ------------------

def spawn_carrot_block(a, b, c, d):
	def task():
		return carrot_worker(a, b, c, d)
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
	# 规划 need+1 个块（31 台子机 + 主机 1 块）
	blocks = plan_carrot_blocks(need + 1)
	# 打印派工计划
	quick_print("DRONES_PLANNED", need, "MAX", need, "SLOTS", free, "", "")
	i = 0
	while i < need:
		b = blocks[i]
		quick_print("DRONE", i + 1, "CARROT_BLOCK", "FROM", b[0], b[1], "TO", b[2], b[3])
		i = i + 1
	# 派发子机
	dispatched = 0
	j = 0
	while j < need:
		bb = blocks[j]
		ok = spawn_carrot_block(bb[0], bb[1], bb[2], bb[3])
		if ok:
			dispatched = dispatched + 1
		j = j + 1
	quick_print("DRONES_DISPATCHED", dispatched, "OF", need, "", "", "", "")
	# 主机接最后一个块（若不足 need+1，接第一个；再不足则接全图）
	if len(blocks) >= need + 1:
		gb = blocks[need]
	else:
		if len(blocks) > 0:
			gb = blocks[0]
		else:
			n = get_world_size()
			gb = (0, 0, n - 1, n - 1)
	quick_print("MAIN_TAKES", gb[0], gb[1], gb[2], gb[3], "", "", "")
	carrot_worker(gb[0], gb[1], gb[2], gb[3])

main()
