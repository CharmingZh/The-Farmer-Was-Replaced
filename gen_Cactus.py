# =================================================================
#  32 线程 · 全局排序收割仙人掌 (Cactus) v1.0
#  - 16 行工 + 16 列工（其中 15 列工为子机，1 列工由主机执行）
#  - 1 收割队长（子机），只在全局成熟且有序时触发一次性递归收割
#  - 无 int()/sleep()/random_int()，纯原生命令集
# =================================================================

# ------------------ 基础移动 ------------------

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

# ------------------ 基础操作 ------------------

def ensure_cactus_here():
	if get_ground_type() != Grounds.Soil:
		till()
	if get_entity_type() != Entities.Cactus:
		plant(Entities.Cactus)

def compare_and_swap_east_ascending():
	# 当前位置与东侧：若本格>东侧，则交换以保证左→右非降
	if get_entity_type() != Entities.Cactus:
		ensure_cactus_here()
	se = measure(East)
	if se != None:
		cv = measure()
		if cv != None:
			if cv > se:
				swap(East)

def compare_and_swap_west_ascending():
	# 当前位置与西侧：若西侧>本格，则向西交换
	if get_entity_type() != Entities.Cactus:
		ensure_cactus_here()
	sw = measure(West)
	if sw != None:
		cv = measure()
		if cv != None:
			if sw > cv:
				swap(West)

def compare_and_swap_north_ascending():
	# 当前位置与北侧：若本格>北侧，则交换以保证下→上非降
	if get_entity_type() != Entities.Cactus:
		ensure_cactus_here()
	sn = measure(North)
	if sn != None:
		cv = measure()
		if cv != None:
			if cv > sn:
				swap(North)

def compare_and_swap_south_ascending():
	# 当前位置与南侧：若南侧>本格，则向南交换
	if get_entity_type() != Entities.Cactus:
		ensure_cactus_here()
	ss = measure(South)
	if ss != None:
		cv = measure()
		if cv != None:
			if ss > cv:
				swap(South)

# ------------------ 行/列 局部排序循环 ------------------
# 采用“往返冒泡”：一趟 左→右 比较交换，再一趟 右→左；列同理
# 通过 16 行、16 列线程长期交替，整体会收敛到二维非降（满足递归收割条件）

def row_sort_pass(y, n):
	# 从左到右
	x = 0
	while x < n - 1:
		move_to(x, y)
		ensure_cactus_here()
		compare_and_swap_east_ascending()
		x = x + 1
	# 从右到左
	x2 = n - 1
	while x2 > 0:
		move_to(x2, y)
		ensure_cactus_here()
		compare_and_swap_west_ascending()
		x2 = x2 - 1

def col_sort_pass(x, n):
	# 从下到上
	y = 0
	while y < n - 1:
		move_to(x, y)
		ensure_cactus_here()
		compare_and_swap_north_ascending()
		y = y + 1
	# 从上到下
	y2 = n - 1
	while y2 > 0:
		move_to(x, y2)
		ensure_cactus_here()
		compare_and_swap_south_ascending()
		y2 = y2 - 1

# ------------------ 工人线程 ------------------

def row_worker(start_row, stride):
	n = get_world_size()
	quick_print("ROW_WORKER", start_row, "STRIDE", stride, "N", n, "", "")
	while True:
		y = start_row
		while y < n:
			row_sort_pass(y, n)
			y = y + stride

def col_worker(start_col, stride):
	n = get_world_size()
	quick_print("COL_WORKER", start_col, "STRIDE", stride, "N", n, "", "")
	while True:
		x = start_col
		while x < n:
			col_sort_pass(x, n)
			x = x + stride

# ------------------ 全局检测：是否“成熟且有序” ------------------

def rows_nondecreasing(n):
	# 行检查：左→右 非降
	y = 0
	while y < n:
		x = 0
		while x < n - 1:
			move_to(x, y)
			if get_entity_type() != Entities.Cactus:
				return False
			if not can_harvest():
				return False
			a = measure()
			b = measure(East)
			if a == None or b == None:
				return False
			if a > b:
				return False
			x = x + 1
		y = y + 1
	return True

def cols_nondecreasing(n):
	# 列检查：下→上 非降
	x = 0
	while x < n:
		y = 0
		while y < n - 1:
			move_to(x, y)
			if get_entity_type() != Entities.Cactus:
				return False
			if not can_harvest():
				return False
			a = measure()
			b = measure(North)
			if a == None or b == None:
				return False
			if a > b:
				return False
			y = y + 1
		x = x + 1
	return True

def fully_sorted_and_mature(n):
	# 同时满足：全是仙人掌 + 全可收 + 行非降 + 列非降
	if not rows_nondecreasing(n):
		return False
	if not cols_nondecreasing(n):
		return False
	return True

def harvest_captain():
	n = get_world_size()
	quick_print("CAPTAIN_START", "CHECKING_SORT+MATURE", "N", n, "", "", "")
	while True:
		ok = fully_sorted_and_mature(n)
		if ok:
			# 递归收割触发点：任意一株；用 (0,0) 更简单可靠
			move_to(0, 0)
			if can_harvest():
				harvest()
				quick_print("GLOBAL_HARVEST_TRIGGERED", "OK", "", "", "", "", "")
		# 轻量延时，避免过度占用 CPU
		k = 0
		while k < 800:
			k = k + 1

# ------------------ 生成子机 ------------------

def spawn_row_worker(s, t):
	def task():
		return row_worker(s, t)
	return spawn_drone(task)

def spawn_col_worker(s, t):
	def task():
		return col_worker(s, t)
	return spawn_drone(task)

def spawn_captain():
	def task():
		return harvest_captain()
	return spawn_drone(task)

# ------------------ 主程序 ------------------

def main():
	set_execution_speed(0)
	n = get_world_size()
	quick_print("START_CACTUS_GLOBAL_SORT", "WORLD", n, "THREADS", 32, "", "", "")

	# 总可生成子机
	want_children = 31
	avail = max_drones() - num_drones()
	if avail < want_children:
		want_children = avail

	# 计划：
	# - 先放 16 个“行工”，stride=16；覆盖 y = 0..n-1
	# - 再放 15 个“列工”（留 1 个列工由主机执行），stride=16
	# - 再放 1 个“收割队长”
	spawned = 0

	# 16 行工
	r = 0
	while r < 16 and spawned < want_children:
		if spawn_row_worker(r, 16):
			spawned = spawned + 1
		r = r + 1

	# 15 列工（0..14），第 16 个列工由主机跑
	c = 0
	while c < 15 and spawned < want_children:
		if spawn_col_worker(c, 16):
			spawned = spawned + 1
		c = c + 1

	# 1 收割队长
	if spawned < want_children:
		if spawn_captain():
			spawned = spawned + 1

	quick_print("CHILDREN_SPAWNED", spawned, "OF", want_children, "", "", "", "")

	# 主机跑“最后一个列工”（start_col=15, stride=16）
	col_worker(15, 16)

while True:
	main()
