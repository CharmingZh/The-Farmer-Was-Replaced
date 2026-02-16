# =================================================================
#   全地图灌木种植 & 巨型迷宫一键生成
#   启动自检：判断当前在迷宫内/外 → 选择阶段进入
#   单机解迷（Trémaux + 走廊压缩）
#   并行逻辑完整保留（默认关闭），后续可一键启用
# =================================================================

# ---------------- 调试输出（固定8参数，无默认值） ----------------
DEBUG = 1
def QP(a, b, c, d, e, f, g, h):
	if DEBUG == 1:
		quick_print(a, b, c, d, e, f, g, h)

def dir_to_str(d):
	if d == North:
		return "N"
	if d == South:
		return "S"
	if d == East:
		return "E"
	if d == West:
		return "W"
	return "?"

# -------------------- 通用/移动/采集工具 --------------------

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

def find_harvestable_grass():
	n = get_world_size()
	y = 0
	while y < n:
		x_start = 0
		x_end = n
		x_step = 1
		if y % 2 != 0:
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

# [x0..x1]×[y0..y1] 蛇形补植为灌木（保留：并行阶段会用）
def ensure_bush_region(x0, y0, x1, y1):
	bush_cost = get_cost(Entities.Bush)
	if bush_cost == None:
		quick_print("错误：无法获取灌木成本。", "", "", "", "", "", "", "")
		return False
	yy = y0
	while yy <= y1:
		xs = x0
		xe = x1 + 1
		st = 1
		if (yy - y0) % 2 != 0:
			xs = x1
			xe = x0 - 1
			st = -1
		xx = xs
		while xx != xe:
			move_to(xx, yy)
			if get_entity_type() != Entities.Bush:
				while (Items.Hay in bush_cost and num_items(Items.Hay) < bush_cost[Items.Hay]) or (Items.Wood in bush_cost and num_items(Items.Wood) < bush_cost[Items.Wood]):
					curx = xx
					cury = yy
					posg = find_harvestable_grass()
					if posg != None:
						harvest()
						move_to(curx, cury)
					else:
						move_to(curx, cury)
						break
				if get_ground_type() != Grounds.Soil:
					till()
				plant(Entities.Bush)
			xx = xx + st
		yy = yy + 1
	return True

# 等待区域内全部灌木成熟（保留：并行阶段会用）
def wait_bush_mature_region(x0, y0, x1, y1):
	while True:
		all_m = True
		yy = y0
		while yy <= y1:
			xs = x0
			xe = x1 + 1
			st = 1
			if (yy - y0) % 2 != 0:
				xs = x1
				xe = x0 - 1
				st = -1
			xx = xs
			while xx != xe:
				move_to(xx, yy)
				if get_entity_type() == Entities.Bush and not can_harvest():
					all_m = False
					break
				xx = xx + st
			if not all_m:
				break
			yy = yy + 1
		if all_m:
			return
		quick_print("区域仍有未成熟灌木，继续等待...", "", "", "", "", "", "", "")

# -------------------- 单格灌木：只在当前位置保证一棵 --------------------

def ensure_single_bush_here():
	bush_cost = get_cost(Entities.Bush)
	if bush_cost == None:
		quick_print("错误：无法获取灌木成本。", "", "", "", "", "", "", "")
		return False
	if get_entity_type() != Entities.Bush:
		need_hay = 0
		need_wood = 0
		if Items.Hay in bush_cost:
			need_hay = bush_cost[Items.Hay]
		if Items.Wood in bush_cost:
			need_wood = bush_cost[Items.Wood]
		safe_guard = get_world_size() * get_world_size() + 10
		loops = 0
		while ((Items.Hay in bush_cost and num_items(Items.Hay) < need_hay) or (Items.Wood in bush_cost and num_items(Items.Wood) < need_wood)) and loops < safe_guard:
			ox = get_pos_x()
			oy = get_pos_y()
			posg = find_harvestable_grass()
			if posg != None:
				harvest()
				move_to(ox, oy)
			else:
				move_to(ox, oy)
				break
			loops = loops + 1
		if get_ground_type() != Grounds.Soil:
			till()
		plant(Entities.Bush)
	if get_entity_type() != Entities.Bush:
		quick_print("单格灌木保障失败。", "", "", "", "", "", "", "")
		return False
	return True

# -------------------- 迷宫一次性生成（基于当前位置） --------------------

def generate_giant_maze_once():
	n = get_world_size()
	min_substance = n + n
	quick_print("检查 Weird_Substance，目标 ≥ ", min_substance, "。", "", "", "", "", "")
	if num_items(Items.Weird_Substance) < min_substance:
		quick_print("Weird_Substance 不足：", num_items(Items.Weird_Substance), "/", min_substance, "，等待产出...", "", "", "")
		return False
	quick_print("一次性生成巨型迷宫于当前位置，尺寸 ", n, "×", n, "...", "", "", "")
	use_item(Items.Weird_Substance, n)
	if measure() == None:
		quick_print("错误：use_item 后未检测到迷宫。", "", "", "", "", "", "", "")
		return False
	quick_print("巨型迷宫生成成功！", "", "", "", "", "", "", "")
	return True

# -------------------- Trémaux + 走廊压缩（含调试打印） --------------------

def get_opposite_direction(direction):
	if direction == North:
		return South
	if direction == South:
		return North
	if direction == East:
		return West
	if direction == West:
		return East
	return None

def apply_direction(x, y, direction):
	if direction == North:
		return (x, y + 1)
	if direction == South:
		return (x, y - 1)
	if direction == East:
		return (x + 1, y)
	if direction == West:
		return (x - 1, y)
	return (x, y)

def ordered_dirs_towards(cx, cy, gx, gy):
	base = [North, East, South, West]
	order = []
	dx = gx - cx
	dy = gy - cy
	if dy > 0:
		order.append(North)
	if dy < 0:
		order.append(South)
	if dx > 0:
		order.append(East)
	if dx < 0:
		order.append(West)
	i = 0
	while i < len(base):
		d = base[i]
		j = 0
		found = False
		while j < len(order):
			if order[j] == d:
				found = True
				break
			j = j + 1
		if not found:
			order.append(d)
		i = i + 1
	return order

VISIT_count = {}
def inc_visit(x, y):
	p = (x, y)
	if p in VISIT_count:
		VISIT_count[p] = VISIT_count[p] + 1
	else:
		VISIT_count[p] = 1

def paint_if_first_visit(cx, cy):
	p = (cx, cy)
	if p in VISIT_count and VISIT_count[p] == 1:
		if get_ground_type() != Grounds.Soil:
			till()

EDGE_MARK = {}
def edge_key(ax, ay, bx, by):
	if ax < bx:
		return ((ax, ay), (bx, by))
	if ax > bx:
		return ((bx, by), (ax, ay))
	if ay <= by:
		return ((ax, ay), (bx, by))
	return ((bx, by), (ax, ay))

def get_edge_mark(ax, ay, bx, by):
	k = edge_key(ax, ay, bx, by)
	if k in EDGE_MARK:
		return EDGE_MARK[k]
	return 0

def inc_edge_mark(ax, ay, bx, by):
	k = edge_key(ax, ay, bx, by)
	if k in EDGE_MARK:
		EDGE_MARK[k] = EDGE_MARK[k] + 1
	else:
		EDGE_MARK[k] = 1

def sprint_corridor(dir, gx, gy):
	if dir == None:
		return (get_pos_x(), get_pos_y(), 0, None)
	while True:
		if not can_move(dir):
			QP("撞墙@冲刺", dir_to_str(dir), "", "", "", "", "", "")
			return (get_pos_x(), get_pos_y(), 1, get_opposite_direction(dir))
		px = get_pos_x()
		py = get_pos_y()
		nxy = apply_direction(px, py, dir)
		nx = nxy[0]
		ny = nxy[1]
		inc_edge_mark(px, py, nx, ny)
		QP("冲刺", dir_to_str(dir), "边+", px, py, "->", nx, ny)
		move(dir)
		cx = get_pos_x()
		cy = get_pos_y()
		inc_visit(cx, cy)
		paint_if_first_visit(cx, cy)
		if cx == gx and cy == gy:
			QP("命中目标@冲刺", cx, cy, "", "", "", "", "")
			harvest()
			return (cx, cy, 3, None)
		back = get_opposite_direction(dir)
		cnt = 0
		next_dir = None
		dirs = [North, East, South, West]
		i = 0
		while i < len(dirs):
			d = dirs[i]
			if d != back and can_move(d):
				cnt = cnt + 1
				next_dir = d
			i = i + 1
		if cnt == 1:
			dir = next_dir
			continue
		if cnt >= 2:
			QP("到分叉", cx, cy, "来路", dir_to_str(back), "", "", "")
			return (cx, cy, 2, back)
		QP("尽头", cx, cy, "回退向", dir_to_str(back), "", "", "")
		return (cx, cy, 1, back)

def choose_next_dir(cx, cy, gx, gy, back_dir):
	cands0 = []
	cands1 = []
	candsX = []
	order = ordered_dirs_towards(cx, cy, gx, gy)
	i = 0
	while i < len(order):
		d = order[i]
		nxy = apply_direction(cx, cy, d)
		nx = nxy[0]
		ny = nxy[1]
		if can_move(d):
			m = get_edge_mark(cx, cy, nx, ny)
			if nx == gx and ny == gy:
				QP("相邻即目标", cx, cy, "->", nx, ny, dir_to_str(d), "")
				return d
			if m == 0:
				cands0.append(d)
			elif m == 1:
				cands1.append(d)
			else:
				candsX.append(d)
		i = i + 1
	if len(cands0) > 0:
		i2 = 0
		while i2 < len(cands0):
			if back_dir != None and cands0[i2] == back_dir:
				i2 = i2 + 1
				continue
			QP("选0边", dir_to_str(cands0[i2]), "", "", "", "", "", "")
			return cands0[i2]
		QP("选0边(仅回头)", dir_to_str(cands0[0]), "", "", "", "", "", "")
		return cands0[0]
	if len(cands1) > 0:
		i3 = 0
		while i3 < len(cands1):
			if back_dir != None and cands1[i3] == back_dir:
				i3 = i3 + 1
				continue
			QP("选1边", dir_to_str(cands1[i3]), "", "", "", "", "", "")
			return cands1[i3]
		QP("选1边(仅回头)", dir_to_str(cands1[0]), "", "", "", "", "", "")
		return cands1[0]
	if back_dir != None and can_move(back_dir):
		QP("无0/1边→回头", dir_to_str(back_dir), "", "", "", "", "", "")
		return back_dir
	if len(candsX) > 0:
		QP("兜底选X边", dir_to_str(candsX[0]), "", "", "", "", "", "")
		return candsX[0]
	QP("无路", cx, cy, "", "", "", "", "")
	return None

def solve_maze_tremaux_once():
	goal = measure()
	if goal == None:
		quick_print("错误：measure() 未返回迷宫坐标。", "", "", "", "", "", "", "")
		return False
	gx = goal[0]
	gy = goal[1]
	global VISIT_count
	global EDGE_MARK
	VISIT_count = {}
	EDGE_MARK = {}
	cx = get_pos_x()
	cy = get_pos_y()
	inc_visit(cx, cy)
	paint_if_first_visit(cx, cy)
	QP("起点", cx, cy, "目标", gx, gy, "", "")
	if cx == gx and cy == gy:
		harvest()
		return True
	back_dir = None
	limit = get_world_size() * get_world_size() * 4
	steps = 0
	while True:
		cx = get_pos_x()
		cy = get_pos_y()
		if cx == gx and cy == gy:
			QP("命中目标@", cx, cy, "", "", "", "", "")
			harvest()
			return True
		dir = choose_next_dir(cx, cy, gx, gy, back_dir)
		if dir == None:
			quick_print("搜索失败：节点无任何可走边。", "", "", "", "", "", "", "")
			return False
		QP("进入方向", dir_to_str(dir), "from", cx, cy, "", "", "")
		res = sprint_corridor(dir, gx, gy)
		if res[2] == 3:
			return True
		cx = res[0]
		cy = res[1]
		new_back = res[3]
		if new_back != None:
			back_dir = new_back
		else:
			back_dir = get_opposite_direction(dir)
		QP("停在", cx, cy, "来路", dir_to_str(back_dir), "", "", "")
		steps = steps + 1
		if steps > limit:
			quick_print("触发安全阈值，终止。", "", "", "", "", "", "", "")
			return False

# --------------- 自适应多无人机：地图切片 & 派发（完整保留，默认不用） ---------------

REGIONS = {}
WORKER_COUNT = 1

def build_regions(K):
	global REGIONS
	REGIONS = {}
	n = get_world_size()
	R = 1
	C = K
	r = 1
	while r * r <= K:
		R = r
		r = r + 1
	C = K // R
	if (R * C) < K:
		C = C + 1
	row_heights = []
	base_h = n // R
	extra = n - base_h * R
	i = 0
	while i < R:
		h = base_h
		if i < extra:
			h = h + 1
		row_heights.append(h)
		i = i + 1
	col_widths = []
	base_w = n // C
	extra_w = n - base_w * C
	j = 0
	while j < C:
		w = base_w
		if j < extra_w:
			w = w + 1
		col_widths.append(w)
		j = j + 1
	y = 0
	idx = 0
	ri = 0
	while ri < R:
		x = 0
		rh = row_heights[ri]
		cj = 0
		while cj < C:
			if idx >= K:
				break
			cw = col_widths[cj]
			x0 = x
			y0 = y
			x1 = x + cw - 1
			y1 = y + rh - 1
			REGIONS[idx] = (x0, y0, x1, y1)
			idx = idx + 1
			x = x + cw
			cj = cj + 1
		y = y + rh
		ri = ri + 1

def region_worker_once(region_id):
	if not (region_id in REGIONS):
		QP("区域不存在", region_id, "", "", "", "", "", "")
		return
	b = REGIONS[region_id]
	x0 = b[0]
	y0 = b[1]
	x1 = b[2]
	y1 = b[3]
	quick_print("Q", region_id, "：开始补植/成熟检查...", "", "", "", "", "", "")
	ensure_bush_region(x0, y0, x1, y1)
	wait_bush_mature_region(x0, y0, x1, y1)
	quick_print("Q", region_id, "：本区域完成，退出。", "", "", "", "", "", "")

def worker_1():
	region_worker_once(1)
def worker_2():
	region_worker_once(2)
def worker_3():
	region_worker_once(3)
def worker_4():
	region_worker_once(4)
def worker_5():
	region_worker_once(5)
def worker_6():
	region_worker_once(6)
def worker_7():
	region_worker_once(7)
def worker_8():
	region_worker_once(8)
def worker_9():
	region_worker_once(9)
def worker_10():
	region_worker_once(10)
def worker_11():
	region_worker_once(11)
def worker_12():
	region_worker_once(12)
def worker_13():
	region_worker_once(13)
def worker_14():
	region_worker_once(14)
def worker_15():
	region_worker_once(15)
def worker_16():
	region_worker_once(16)
def worker_17():
	region_worker_once(17)
def worker_18():
	region_worker_once(18)
def worker_19():
	region_worker_once(19)
def worker_20():
	region_worker_once(20)
def worker_21():
	region_worker_once(21)
def worker_22():
	region_worker_once(22)
def worker_23():
	region_worker_once(23)
def worker_24():
	region_worker_once(24)
def worker_25():
	region_worker_once(25)
def worker_26():
	region_worker_once(26)
def worker_27():
	region_worker_once(27)
def worker_28():
	region_worker_once(28)
def worker_29():
	region_worker_once(29)
def worker_30():
	region_worker_once(30)
def worker_31():
	region_worker_once(31)

def spawn_workers_for_K(K):
	i = 1
	while i < K:
		if num_drones() < max_drones():
			if i == 1:
				spawn_drone(worker_1)
			elif i == 2:
				spawn_drone(worker_2)
			elif i == 3:
				spawn_drone(worker_3)
			elif i == 4:
				spawn_drone(worker_4)
			elif i == 5:
				spawn_drone(worker_5)
			elif i == 6:
				spawn_drone(worker_6)
			elif i == 7:
				spawn_drone(worker_7)
			elif i == 8:
				spawn_drone(worker_8)
			elif i == 9:
				spawn_drone(worker_9)
			elif i == 10:
				spawn_drone(worker_10)
			elif i == 11:
				spawn_drone(worker_11)
			elif i == 12:
				spawn_drone(worker_12)
			elif i == 13:
				spawn_drone(worker_13)
			elif i == 14:
				spawn_drone(worker_14)
			elif i == 15:
				spawn_drone(worker_15)
			elif i == 16:
				spawn_drone(worker_16)
			elif i == 17:
				spawn_drone(worker_17)
			elif i == 18:
				spawn_drone(worker_18)
			elif i == 19:
				spawn_drone(worker_19)
			elif i == 20:
				spawn_drone(worker_20)
			elif i == 21:
				spawn_drone(worker_21)
			elif i == 22:
				spawn_drone(worker_22)
			elif i == 23:
				spawn_drone(worker_23)
			elif i == 24:
				spawn_drone(worker_24)
			elif i == 25:
				spawn_drone(worker_25)
			elif i == 26:
				spawn_drone(worker_26)
			elif i == 27:
				spawn_drone(worker_27)
			elif i == 28:
				spawn_drone(worker_28)
			elif i == 29:
				spawn_drone(worker_29)
			elif i == 30:
				spawn_drone(worker_30)
			elif i == 31:
				spawn_drone(worker_31)
			else:
				quick_print("包装函数不足，请扩展 worker_32+ ", "", "", "", "", "", "", "")
		i = i + 1

# -------------------- 环境状态判定 --------------------

def in_maze_now():
	g = measure()
	if g == None:
		return False
	return True

# -------------------- 启动器（阶段自适应） --------------------

def main():
	quick_print("== 自适应启动：迷宫内/外判定 ==", "", "", "", "", "", "", "")
	if num_unlocked(Unlocks.Costs) == 0:
		unlock(Unlocks.Costs)
	if num_unlocked(Unlocks.Mazes) == 0:
		unlock(Unlocks.Mazes)

	USE_PARALLEL = 0

	while True:
		if in_maze_now():
			QP("状态", "在迷宫内", "", "", "", "", "", "")
			if not solve_maze_tremaux_once():
				quick_print("解迷未成功，下一轮继续尝试。", "", "", "", "", "", "", "")
			continue

		QP("状态", "在迷宫外", "", "", "", "", "", "")

		if USE_PARALLEL == 1:
			global WORKER_COUNT
			K_cap = max_drones()
			if K_cap < 1:
				K_cap = 1
			MAX_WRAPPERS = 31
			K = K_cap
			if K > (MAX_WRAPPERS + 1):
				K = MAX_WRAPPERS + 1
			WORKER_COUNT = K
			build_regions(K)
			QP("并行切片数", K, "max_drones", max_drones(), "", "", "", "")
			spawn_workers_for_K(K)
			region_worker_once(0)
			while num_drones() > 1:
				pass
		else:
			if not ensure_single_bush_here():
				quick_print("单点灌木失败，下一轮重试。", "", "", "", "", "", "", "")
				continue

		if not generate_giant_maze_once():
			quick_print("资源不足或生成失败，下一轮重试迷宫生成。", "", "", "", "", "", "", "")
			continue

		if not solve_maze_tremaux_once():
			quick_print("解迷未成功，下一轮重试。", "", "", "", "", "", "", "")

# -------------------- 脚本入口 --------------------
main()
