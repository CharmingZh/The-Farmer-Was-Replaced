# =================================================================
#  并行迷宫（多级派发版）
#  - 父机集中记忆（EXPLORED/CLAIMED）避免父机重复派发
#  - 子机也能在分叉处继续派子机；并发满则句柄等待
#  - 任意时刻 measure()==None → 立刻返回；不路过宝藏
#  - 目标：尽可能吃满 max_drones()（如 8）
# =================================================================

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

# ---------------- 基础工具 ----------------

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

def edge_key(ax, ay, bx, by):
	if ax < bx:
		return ((ax, ay), (bx, by))
	if ax > bx:
		return ((bx, by), (ax, ay))
	if ay <= by:
		return ((ax, ay), (bx, by))
	return ((bx, by), (ax, ay))

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

# ---------------- 造图/前置 ----------------

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

def ensure_single_bush_here():
	cost = get_cost(Entities.Bush)
	if cost == None:
		QP("错误", "灌木成本nil", "", "", "", "", "", "")
		return False
	if get_entity_type() != Entities.Bush:
		need_hay = 0
		need_wood = 0
		if Items.Hay in cost:
			need_hay = cost[Items.Hay]
		if Items.Wood in cost:
			need_wood = cost[Items.Wood]
		guard = get_world_size() * get_world_size() + 10
		loops = 0
		while ((Items.Hay in cost and num_items(Items.Hay) < need_hay) or (Items.Wood in cost and num_items(Items.Wood) < need_wood)) and loops < guard:
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
		QP("错误", "灌木失败", "", "", "", "", "", "")
		return False
	return True

def generate_giant_maze_once():
	n = get_world_size() * get_world_size()
	need = n 
	cur = num_items(Items.Weird_Substance)
	QP("检查Weird", "需≥", need, "现有", cur, "", "", "")
	if cur < need:
		QP("Weird不足", cur, "/", need, "等待", "", "", "")
		return False
	QP("生成迷宫", "尺寸", n, "×", n, "于此", "", "")
	use_item(Items.Weird_Substance, n)
	if measure() == None:
		QP("错误", "生成失败", "", "", "", "", "", "")
		return False
	QP("生成成功", "", "", "", "", "", "", "")
	return True

# ---------------- 父机集中记忆（仅父机使用） ----------------

EXPLORED_EDGES = {}
CLAIMED_EDGES = {}

def explored_has(ax, ay, bx, by):
	return edge_key(ax, ay, bx, by) in EXPLORED_EDGES

def explored_add_path(path):
	i = 0
	while i < len(path):
		EXPLORED_EDGES[path[i]] = 1
		i = i + 1

def claimed_has(ax, ay, bx, by):
	return edge_key(ax, ay, bx, by) in CLAIMED_EDGES

def claimed_add(ax, ay, bx, by):
	CLAIMED_EDGES[edge_key(ax, ay, bx, by)] = 1

def claimed_remove_path(path):
	i = 0
	while i < len(path):
		k = path[i]
		if k in CLAIMED_EDGES:
			CLAIMED_EDGES.pop(k)
		i = i + 1

# ---------------- 子机：多级派发（小父机） ----------------
# 返回 ("win", path) / ("deadend", path) / ("abort", path)
# 子机内有自己的去重：explored_local / claimed_local

def child_solver(initial_dir, gx, gy):
	if measure() == None:
		return ("abort", [])
	path = []
	explored_local = {}
	claimed_local = {}

	def explored_l_has(k):
		return k in explored_local

	def explored_l_add_path(p):
		i = 0
		while i < len(p):
			explored_local[p[i]] = 1
			i = i + 1

	def claimed_l_has(k):
		return k in claimed_local

	def claimed_l_add(k):
		claimed_local[k] = 1

	def claimed_l_remove_path(p):
		i = 0
		while i < len(p):
			k = p[i]
			if k in claimed_local:
				claimed_local.pop(k)
			i = i + 1

	def sprint_or_branch(dir0):
		local_path = []
		if dir0 == None:
			return ("deadend", local_path)
		d = dir0
		while True:
			if measure() == None:
				return ("abort", local_path)
			if not can_move(d):
				return ("deadend", local_path)
			px = get_pos_x()
			py = get_pos_y()
			nx, ny = apply_direction(px, py, d)
			ek = edge_key(px, py, nx, ny)
			# 下一格宝藏
			if nx == gx and ny == gy:
				move(d)
				local_path.append(ek)
				harvest()
				return ("win", local_path)
			# 正常走一步
			move(d)
			local_path.append(ek)
			if measure() == None:
				return ("abort", local_path)
			cx = get_pos_x()
			cy = get_pos_y()
			back = get_opposite_direction(d)
			# 查看非回头可走邻边数（0-边定义：可走，且未在 explored_local/claimed_local）
			cnt = 0
			next_dir = None
			dirs = [North, East, South, West]
			i = 0
			while i < len(dirs):
				dd = dirs[i]
				if dd != back and can_move(dd):
					tx, ty = apply_direction(cx, cy, dd)
					kk = edge_key(cx, cy, tx, ty)
					if (not explored_l_has(kk)) and (not claimed_l_has(kk)):
						cnt = cnt + 1
						next_dir = dd
				i = i + 1
			if cnt == 1:
				d = next_dir
				continue
			# 分叉或尽头
			return ("deadend", local_path)

	# 若初始方向非空，先冲一段（避免在父机节点里重复计算）
	if initial_dir != None:
		status, pth = sprint_or_branch(initial_dir)
		if status == "win":
			return ("win", pth)
		if status != "deadend":
			# abort 等
			return (status, pth)
		# deadend：把这段路径计入 explored_local，再继续在当前节点做派发
		explored_l_add_path(pth)
		# 回到当前位置继续（当前位置就是冲刺停止处）

	# 子机主循环：和父机同结构，但仅使用“局部去重”
	while True:
		if measure() == None:
			return ("abort", path)
		cx = get_pos_x()
		cy = get_pos_y()
		# 命中宝藏（少见：可能初始就在宝藏上）
		g = measure()
		if g != None and cx == g[0] and cy == g[1]:
			harvest()
			return ("win", path)

		# 选候选边（本地去重）
		order = ordered_dirs_towards(cx, cy, gx, gy)
		cands = []
		i = 0
		while i < len(order):
			d = order[i]
			if can_move(d):
				tx, ty = apply_direction(cx, cy, d)
				kk = edge_key(cx, cy, tx, ty)
				if (not explored_l_has(kk)) and (not claimed_l_has(kk)):
					cands.append(d)
			i = i + 1

		if len(cands) == 0:
			# 把自己累计的 path 交回父层
			return ("deadend", path)

		if len(cands) == 1:
			d = cands[0]
			status, pth = sprint_or_branch(d)
			# 合并到累计路径
			i2 = 0
			while i2 < len(pth):
				path.append(pth[i2])
				i2 = i2 + 1
			if status == "win":
				return ("win", path)
			if status == "deadend":
				explored_l_add_path(pth)
				continue
			return (status, path)

		# 分叉：主方向先不走，先把其它方向尽可能派出去；并发满就等
		main_dir = cands[0]
		others = []
		i = 1
		while i < len(cands):
			others.append(cands[i])
			i = i + 1

		children = []
		k = 0
		while k < len(others):
			d = others[k]
			tx, ty = apply_direction(cx, cy, d)
			kk = edge_key(cx, cy, tx, ty)
			claimed_l_add(kk)

			def wrap(dcap, gxcap, gycap):
				def worker():
					return child_solver(dcap, gxcap, gycap)
				return worker

			h = spawn_drone(wrap(d, gx, gy))
			if h:
				children.append(h)
				QP("子机派子", dir_to_str(d), "from", cx, cy, "kids", len(children), "")
				k = k + 1
			else:
				# 并发满：等一个完成
				QP("子机并发满", "等待", "need", len(others)-k, "alive", len(children), "", "")
				idx = 0
				waited = False
				while idx < len(children):
					if has_finished(children[idx]):
						res = wait_for(children[idx])
						# 清本地 claimed；并把返回路径并入“已探索本地”
						if res != None and res != False:
							if res[0] == "win":
								QP("子链胜利", "上返win", "", "", "", "", "", "")
								return ("win", path)
							else:
								# 失败路径合并
								claimed_l_remove_path(res[1])
								explored_l_add_path(res[1])
						children.pop(idx)
						waited = True
						break
					idx = idx + 1
				if not waited:
					QP("子机等待", "未完成", "kids", len(children), "", "", "", "")

		# 主方向自己走
		status, pth = sprint_or_branch(main_dir)
		i3 = 0
		while i3 < len(pth):
			path.append(pth[i3])
			i3 = i3 + 1
		if status == "win":
			return ("win", path)
		if status == "deadend":
			explored_l_add_path(pth)
			# 顺手收割已经结束的孩子
			j = 0
			while j < len(children):
				if has_finished(children[j]):
					res2 = wait_for(children[j])
					if res2 != None and res2 != False:
						if res2[0] == "win":
							return ("win", path)
						else:
							claimed_l_remove_path(res2[1])
							explored_l_add_path(res2[1])
					children.pop(j)
				else:
					j = j + 1
			continue
		return (status, path)

# ---------------- 父机：并行解迷（多级派发入口） ----------------

def parent_solve_maze():
	g = measure()
	if g == None:
		QP("错误", "无迷宫", "", "", "", "", "", "")
		return False
	gx = g[0]
	gy = g[1]

	# 父机循环：在当前节点做“派发至满”为止，再走主路一步
	while True:
		if measure() == None:
			QP("父机终止", "迷宫消失", "", "", "", "", "", "")
			return True
		cx = get_pos_x()
		cy = get_pos_y()
		if cx == gx and cy == gy:
			QP("父机命中", "收获", cx, cy, "", "", "", "")
			harvest()
			return True

		order = ordered_dirs_towards(cx, cy, gx, gy)
		cands = []
		i = 0
		while i < len(order):
			d = order[i]
			if can_move(d):
				tx, ty = apply_direction(cx, cy, d)
				if (not explored_has(cx, cy, tx, ty)) and (not claimed_has(cx, cy, tx, ty)):
					cands.append(d)
			i = i + 1

		if len(cands) == 0:
			QP("父机无路", "结束控制", cx, cy, "", "", "", "")
			return False

		if len(cands) == 1:
			d = cands[0]
			px = get_pos_x()
			py = get_pos_y()
			nx, ny = apply_direction(px, py, d)
			if nx == gx and ny == gy:
				QP("父机下一格宝", px, py, "->", nx, ny, "收获", "")
				move(d)
				harvest()
				return True
			QP("父机直进", dir_to_str(d), px, py, "->", nx, ny, "")
			move(d)
			EXPLORED_EDGES[edge_key(px, py, nx, ny)] = 1
			continue

		main_dir = cands[0]
		others = []
		i = 1
		while i < len(cands):
			others.append(cands[i])
			i = i + 1

		children = []
		k = 0
		while k < len(others):
			d = others[k]
			tx, ty = apply_direction(cx, cy, d)
			claimed_add(cx, cy, tx, ty)

			def wrap(dcap, gxcap, gycap):
				def worker():
					return child_solver(dcap, gxcap, gycap)
				return worker

			h = spawn_drone(wrap(d, gx, gy))
			if h:
				children.append(h)
				QP("派子机", dir_to_str(d), "from", cx, cy, "kids", len(children), "")
				k = k + 1
			else:
				# 撤销占位（没派出去）
				CLAIMED_EDGES.pop(edge_key(cx, cy, tx, ty))
				# 并发满：等一个完成再继续派（保证把当前节点的分支尽可能都派出去）
				QP("并发满", "等待", "need", len(others)-k, "alive", len(children), "", "")
				idx = 0
				waited = False
				while idx < len(children):
					if has_finished(children[idx]):
						res = wait_for(children[idx])
						if res != None and res != False:
							claimed_remove_path(res[1])
							if res[0] == "win":
								QP("子机胜利", "父机退", "", "", "", "", "", "")
								return True
							else:
								explored_add_path(res[1])
						children.pop(idx)
						waited = True
						break
					idx = idx + 1
				if not waited:
					QP("等待中", "未完成", "kids", len(children), "", "", "", "")

		# 主方向自己走一步（不路过）
		px = get_pos_x()
		py = get_pos_y()
		nx, ny = apply_direction(px, py, main_dir)
		if nx == gx and ny == gy:
			QP("父机主路宝", px, py, "->", nx, ny, "收获", "")
			move(main_dir)
			harvest()
			return True
		QP("父机主路", dir_to_str(main_dir), px, py, "->", nx, ny, "")
		move(main_dir)
		EXPLORED_EDGES[edge_key(px, py, nx, ny)] = 1

		# 非阻塞收割已结束的子机
		i2 = 0
		while i2 < len(children):
			if has_finished(children[i2]):
				res2 = wait_for(children[i2])
				if res2 != None and res2 != False:
					claimed_remove_path(res2[1])
					if res2[0] == "win":
						QP("子机胜利", "父机退", "", "", "", "", "", "")
						return True
					else:
						explored_add_path(res2[1])
				children.pop(i2)
			else:
				i2 = i2 + 1

# ---------------- 自适应启动 ----------------

def in_maze_now():
	return (measure() != None)

def main():
	quick_print("== 多级派发并行迷宫 启动 ==", "", "", "", "", "", "", "")
	if num_unlocked(Unlocks.Costs) == 0:
		unlock(Unlocks.Costs)
	if num_unlocked(Unlocks.Mazes) == 0:
		unlock(Unlocks.Mazes)

	while True:
		global EXPLORED_EDGES
		global CLAIMED_EDGES
		EXPLORED_EDGES = {}
		CLAIMED_EDGES = {}
		QP("新轮", "清空记忆", "E", 0, "C", 0, "", "")

		if not in_maze_now():
			QP("状态", "在迷宫外", "", "", "", "", "", "")
			if not ensure_single_bush_here():
				continue
			if not generate_giant_maze_once():
				continue

		QP("状态", "在迷宫内", "", "", "", "", "", "")
		win = parent_solve_maze()

		# 等所有子机自然退出（宝藏收获后 measure()==None）
		spin = 0
		while num_drones() > 1:
			spin = spin + 1
			if spin % 200 == 0:
				QP("清场中", "alive", num_drones(), "win", win, "", "", "")

# 入口
main()
