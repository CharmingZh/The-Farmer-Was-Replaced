# =================================================================
#  并行迷宫（多级派发 · 复用到300次才收割 · 死锁抑制 + 即时退场版）
#  - 任何命宝藏者：REUSE<300 → use_item(MAZE_COST)+trigger_abort()
#                 否则 → harvest()+trigger_abort()
#  - 强硬清场：ABORT_ALL 硬中止 + EPOCH 纪元 + 统一句柄池回收
#  - 防分叉爆炸：Trémaux 边访问计数(≤2) + 节点租约 + 每节点限流 + 全局预算
#  - “目标变更等价于迷宫消失”：复用/收割后所有非宝藏位子机立刻返回，不再跑到死路
#  - 复用后：清节点租约（保持 VISITS），继续在“旧足迹”上推进；真正新一轮才清 VISITS
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

# ---------------- 造图/前置 ----------------

def move_to(tx, ty):
	px = get_pos_x()
	py = get_pos_y()
	while px < tx:
		if ABORT_ALL == 1:
			return
		move(East)
		px = px + 1
	while px > tx:
		if ABORT_ALL == 1:
			return
		move(West)
		px = px - 1
	while py < ty:
		if ABORT_ALL == 1:
			return
		move(North)
		py = py + 1
	while py > ty:
		if ABORT_ALL == 1:
			return
		move(South)
		py = py - 1

def find_harvestable_grass():
	n = get_world_size()
	y = 0
	while y < n:
		if ABORT_ALL == 1:
			return None
		x_start = 0
		x_end = n
		x_step = 1
		if y % 2 != 0:
			x_start = n - 1
			x_end = -1
			x_step = -1
		x = x_start
		while x != x_end:
			if ABORT_ALL == 1:
				return None
			move_to(x, y)
			if get_entity_type() == Entities.Grass and can_harvest():
				return (x, y)
			x = x + x_step
		y = y + 1
	return None

def ensure_single_bush_here():
	if ABORT_ALL == 1:
		return False
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
			if ABORT_ALL == 1:
				return False
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

# ---- 迷宫成本（按文档）----
def compute_maze_cost():
	ws = get_world_size()
	lv = num_unlocked(Unlocks.Mazes)
	if lv < 1:
		lv = 1
	pow2 = 1
	i = 1
	while i < lv:
		pow2 = pow2 * 2
		i = i + 1
	return ws * pow2

# ---- 初始迷宫生成 ----
def generate_initial_maze_once():
	if ABORT_ALL == 1:
		return False
	global MAZE_COST
	MAZE_COST = compute_maze_cost()
	cur = num_items(Items.Weird_Substance)
	QP("检查Weird", "需≥", MAZE_COST, "现有", cur, "", "", "")
	if cur < MAZE_COST:
		QP("Weird不足", cur, "/", MAZE_COST, "等待", "", "", "")
		return False
	if get_entity_type() != Entities.Bush:
		if not ensure_single_bush_here():
			return False
	QP("生成迷宫", "cost", MAZE_COST, "at", get_pos_x(), get_pos_y(), "", "")
	use_item(Items.Weird_Substance, MAZE_COST)
	if measure() == None:
		QP("错误", "生成失败", "", "", "", "", "", "")
		return False
	QP("生成成功", "", "", "", "", "", "", "")
	return True

# ---------------- 集中记忆（Trémaux + 节点租约 + 申领边） ----------------

VISITS = {}          # edge_key -> 0,1,2  （Trémaux）
NODE_LEASE = {}      # (x,y) -> epoch when leased
CLAIMED_EDGES = {}   # 全局申领，防重复派发同边

def visit_get(k):
	if k in VISITS:
		return VISITS[k]
	return 0

def visit_inc(k):
	cnt = visit_get(k)
	if cnt < 2:
		VISITS[k] = cnt + 1

def visit_add_path(path):
	i = 0
	while i < len(path):
		visit_inc(path[i])
		i = i + 1

def can_expand_edge(ax, ay, bx, by):
	return visit_get(edge_key(ax, ay, bx, by)) < 2

def lease_try(cx, cy):
	key = (cx, cy)
	ep = epoch_now()
	if key in NODE_LEASE:
		le = NODE_LEASE[key]
		if le != ep:
			NODE_LEASE[key] = ep
			return True
		return False
	NODE_LEASE[key] = ep
	return True

def lease_release(cx, cy):
	key = (cx, cy)
	if key in NODE_LEASE:
		NODE_LEASE.pop(key)

def memory_reset_after_reuse():
	# 复用后拓扑变动：清节点租约；保留 VISITS（让探索有“记忆”避免回灌）
	global NODE_LEASE
	NODE_LEASE = {}

def reset_all_memory_for_new_round():
	# 真正新一轮时清空所有图记忆
	global VISITS
	global NODE_LEASE
	global CLAIMED_EDGES
	VISITS = {}
	NODE_LEASE = {}
	CLAIMED_EDGES = {}

def claimed_add(ax, ay, bx, by):
	CLAIMED_EDGES[edge_key(ax, ay, bx, by)] = 1

def claimed_has(ax, ay, bx, by):
	return edge_key(ax, ay, bx, by) in CLAIMED_EDGES

def claimed_remove_path(path):
	i = 0
	while i < len(path):
		k = path[i]
		if k in CLAIMED_EDGES:
			CLAIMED_EDGES.pop(k)
		i = i + 1

# ---------------- 并行限流参数 ----------------
MAX_FANOUT_PER_NODE = 3   # 每节点最多派出几个额外子机（主方向自己走）
def global_spawn_budget():
	b = max_drones() - num_drones()
	if b < 0:
		return 0
	return b

# ---------------- 复用控制（纪元/硬中止/句柄池） ----------------
EPOCH = 0
REUSE_COUNT = 0
MAZE_COST = 0
ACTIVE_HANDLES = []
ABORT_ALL = 0

def epoch_now():
	return EPOCH

def bump_epoch():
	global EPOCH
	EPOCH = EPOCH + 1
	QP("EPOCH++", "到", EPOCH, "", "", "", "", "")

def trigger_abort():
	global ABORT_ALL
	ABORT_ALL = 1
	bump_epoch()

def clear_abort():
	global ABORT_ALL
	ABORT_ALL = 0
	QP("ABORT复位", "", "", "", "", "", "", "")

def track_handle(h):
	if h:
		ACTIVE_HANDLES.append(h)

def drain_all_handles():
	i = 0
	alive = 0
	while i < len(ACTIVE_HANDLES):
		h = ACTIVE_HANDLES[i]
		if has_finished(h):
			res = wait_for(h)
			ACTIVE_HANDLES.pop(i)
		else:
			alive = alive + 1
			i = i + 1
	return alive

def wait_all_children_exit():
	rounds = 0
	while True:
		alive_reg = drain_all_handles()
		if num_drones() <= 1 and alive_reg == 0:
			break
		trigger_abort()
		rounds = rounds + 1
		if rounds % 50 == 0:
			QP("清场中", "alive", num_drones(), "reg", alive_reg, "epoch", EPOCH, "")
		if rounds > 2000:
			QP("清场超时", "强行过轮", "alive", num_drones(), "reg", alive_reg, "", "")
			break

def _set_maze_cost(v):
	global MAZE_COST
	MAZE_COST = v

# ---- 命宝藏统一处理 ----
def on_treasure_touch():
	global REUSE_COUNT
	if MAZE_COST <= 0:
		_set_maze_cost(compute_maze_cost())
	if REUSE_COUNT < 300:
		use_item(Items.Weird_Substance, MAZE_COST)
		REUSE_COUNT = REUSE_COUNT + 1
		QP("复用成功", "第", REUSE_COUNT, "次", "cost", MAZE_COST, "", "")
		trigger_abort()
		return "reused"
	else:
		harvest()
		QP("达到300次", "已收割", "", "", "", "", "", "")
		trigger_abort()
		return "done"

# ---- “目标变更等价退出”：复用会搬家，或收割后 measure()==None ----
def treasure_changed_from(gx, gy):
	m = measure()
	if m == None:
		return True
	if m[0] != gx or m[1] != gy:
		return True
	return False

# ---------------- 子机：多级派发（Trémaux + 租约 + 限流 + 目标变更即退） ----------------
# 返回 "reused" / "done" / "deadend" / "abort"
def child_solver(initial_dir, gx, gy, born_epoch):
	if measure() == None:
		return ("abort", [])
	# 复用可能刚发生：目标已变更即退
	if treasure_changed_from(gx, gy):
		return ("abort", [])
	path = []
	explored_local = {}
	claimed_local = {}

	def epoch_invalid():
		return epoch_now() != born_epoch

	def should_abort():
		# 把“目标变更”视为与 measure()==None 等价的退场信号
		return ABORT_ALL == 1 or epoch_invalid() or treasure_changed_from(gx, gy)

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

	def wait_children_locally(children):
		idx = 0
		waited = False
		while idx < len(children):
			if should_abort():
				return ("abort", [])
			if treasure_changed_from(gx, gy):
				return ("abort", [])
			if has_finished(children[idx]):
				res = wait_for(children[idx])
				children.pop(idx)
				waited = True
				if res != None and res != False:
					return (res[0], res[1])
				break
			else:
				idx = idx + 1
		if not waited:
			QP("子机等待", "未完成", "kids", len(children), "", "", "", "")
		drain_all_handles()
		return (None, [])

	def sprint_or_branch(dir0):
		local_path = []
		if dir0 == None:
			return ("deadend", local_path)
		d = dir0
		while True:
			if should_abort():
				return ("abort", local_path)
			if treasure_changed_from(gx, gy):
				return ("abort", local_path)
			if not can_move(d):
				return ("deadend", local_path)
			px = get_pos_x()
			py = get_pos_y()
			nx, ny = apply_direction(px, py, d)
			ek = edge_key(px, py, nx, ny)
			if nx == gx and ny == gy:
				move(d)
				local_path.append(ek)
				stat = on_treasure_touch()
				return (stat, local_path)
			move(d)
			local_path.append(ek)
			if should_abort():
				return ("abort", local_path)
			if treasure_changed_from(gx, gy):
				return ("abort", local_path)
			cx = get_pos_x()
			cy = get_pos_y()
			back = get_opposite_direction(d)
			cnt = 0
			next_dir = None
			dirs = [North, East, South, West]
			i = 0
			while i < len(dirs):
				dd = dirs[i]
				if dd != back and can_move(dd):
					tx, ty = apply_direction(cx, cy, dd)
					kk = edge_key(cx, cy, tx, ty)
					# Trémaux：边访问少于2次，且本地未占/未探索
					if visit_get(kk) < 2 and (not explored_l_has(kk)) and (not claimed_l_has(kk)):
						cnt = cnt + 1
						next_dir = dd
				i = i + 1
			if cnt == 1:
				d = next_dir
				continue
			return ("deadend", local_path)

	# 初始冲刺
	if initial_dir != None:
		status, pth = sprint_or_branch(initial_dir)
		if status == "reused" or status == "done":
			return (status, pth)
		if status != "deadend":
			return (status, pth)
		explored_l_add_path(pth)
		visit_add_path(pth)

	# 子机主循环
	while True:
		if should_abort():
			return ("abort", path)
		if treasure_changed_from(gx, gy):
			return ("abort", path)
		cx = get_pos_x()
		cy = get_pos_y()
		g = measure()
		if g != None and cx == g[0] and cy == g[1]:
			stat2 = on_treasure_touch()
			return (stat2, path)

		# --- 生成候选（Trémaux + 启发式） ---
		order = [North, East, South, West]

		def cand_push(d):
			if can_move(d):
				tx, ty = apply_direction(cx, cy, d)
				kk = edge_key(cx, cy, tx, ty)
				if visit_get(kk) < 2 and (not explored_l_has(kk)) and (not claimed_l_has(kk)):
					return True
			return False

		raw = []
		i = 0
		while i < len(order):
			if cand_push(order[i]):
				raw.append(order[i])
			i = i + 1

		def md_after(d):
			tx, ty = apply_direction(cx, cy, d)
			dx = tx - gx
			if dx < 0:
				dx = -dx
			dy = ty - gy
			if dy < 0:
				dy = -dy
			return dx + dy

		i = 0
		while i < len(raw):
			j = i + 1
			best = i
			while j < len(raw):
				if md_after(raw[j]) < md_after(raw[best]):
					best = j
				j = j + 1
			tmp = raw[i]
			raw[i] = raw[best]
			raw[best] = tmp
			i = i + 1
		cands = raw

		# --- 分叉：节点租约 + 限流 + 预算 ---
		if len(cands) == 0:
			return ("deadend", path)

		if treasure_changed_from(gx, gy):
			return ("abort", path)

		if not lease_try(cx, cy):
			# 节点被占：不派发，自己走主方向
			main_dir = cands[0]
			status, pth = sprint_or_branch(main_dir)
			i2 = 0
			while i2 < len(pth):
				path.append(pth[i2])
				i2 = i2 + 1
			visit_add_path(pth)
			if status == "reused" or status == "done":
				return (status, path)
			if status == "deadend":
				explored_l_add_path(pth)
				continue
			return (status, path)

		main_dir = cands[0]
		others = []
		i = 1
		while i < len(cands):
			others.append(cands[i])
			i = i + 1

		budget = global_spawn_budget()
		fanout = MAX_FANOUT_PER_NODE
		if budget < fanout:
			fanout = budget
		if fanout < 0:
			fanout = 0

		children_dirs = []
		i = 0
		while i < len(others) and i < fanout:
			children_dirs.append(others[i])
			i = i + 1

		children = []
		k = 0
		while k < len(children_dirs):
			if should_abort():
				lease_release(cx, cy)
				return ("abort", path)
			if ABORT_ALL == 1:
				break
			d = children_dirs[k]
			tx, ty = apply_direction(cx, cy, d)
			kk = edge_key(cx, cy, tx, ty)
			claimed_l_add(kk)

			def wrap(dcap, gxcap, gycap, born):
				def worker():
					return child_solver(dcap, gxcap, gycap, born)
				return worker

			h = None
			if ABORT_ALL == 0 and global_spawn_budget() > 0:
				h = spawn_drone(wrap(d, gx, gy, epoch_now()))
			if h:
				track_handle(h)
				children.append(h)
				QP("子机派子(限流)", dir_to_str(d), "from", cx, cy, "kids", len(children), "")
			k = k + 1

		# 主方向自己走一步
		status, pth = sprint_or_branch(main_dir)
		i3 = 0
		while i3 < len(pth):
			path.append(pth[i3])
			i3 = i3 + 1
		visit_add_path(pth)

		if status == "reused" or status == "done":
			lease_release(cx, cy)
			return (status, path)
		if status == "deadend":
			explored_l_add_path(pth)
			# 顺手收割已结束的孩子
			j = 0
			while j < len(children):
				if has_finished(children[j]):
					res2 = wait_for(children[j])
					children.pop(j)
					if res2 != None and res2 != False:
						if res2[0] == "reused" or res2[0] == "done":
							lease_release(cx, cy)
							return (res2[0], path)
						else:
							claimed_l_remove_path(res2[1])
							explored_l_add_path(res2[1])
							visit_add_path(res2[1])
				else:
					j = j + 1
			lease_release(cx, cy)
			continue
		lease_release(cx, cy)
		return (status, path)

# ---------------- 父机：并行解迷（接收复用/收割结果） ----------------

def parent_solve_maze_with_reuse():
	while True:
		if ABORT_ALL == 1:
			wait_all_children_exit()
			clear_abort()
		g = measure()
		if g == None:
			QP("父机", "无迷宫", "", "", "", "", "", "")
			return True
		gx = g[0]
		gy = g[1]

		while True:
			if ABORT_ALL == 1:
				wait_all_children_exit()
				clear_abort()
				memory_reset_after_reuse()
				# 保持 VISITS，不清空；仅清租约，随后继续
				break
			if measure() == None:
				QP("父机终止", "迷宫消失", "", "", "", "", "", "")
				return True
			cx = get_pos_x()
			cy = get_pos_y()

			# 父机站在宝藏：就地处理
			if cx == gx and cy == gy:
				QP("父机命中", "到宝藏", cx, cy, "reuse", REUSE_COUNT, "", "")
				stat0 = on_treasure_touch()
				wait_all_children_exit()
				if stat0 == "reused":
					memory_reset_after_reuse()
					clear_abort()
					break
				else:
					clear_abort()
					return True

			# 生成候选（Trémaux 约束）
			cands = []
			dirs = [North, East, South, West]
			i = 0
			while i < len(dirs):
				d = dirs[i]
				if can_move(d):
					tx, ty = apply_direction(cx, cy, d)
					if can_expand_edge(cx, cy, tx, ty) and (not claimed_has(cx, cy, tx, ty)):
						cands.append(d)
				i = i + 1

			if len(cands) == 0:
				QP("父机无路", "局部死", cx, cy, "", "", "", "")
				return False

			# 按启发式排序（更近的优先）
			def md_after(d):
				tx, ty = apply_direction(cx, cy, d)
				dx = tx - gx
				if dx < 0:
					dx = -dx
				dy = ty - gy
				if dy < 0:
					dy = -dy
				return dx + dy
			i = 0
			while i < len(cands):
				j = i + 1
				best = i
				while j < len(cands):
					if md_after(cands[j]) < md_after(cands[best]):
						best = j
					j = j + 1
				tmp = cands[i]
				cands[i] = cands[best]
				cands[best] = tmp
				i = i + 1

			# 单路：直接走并计数
			if len(cands) == 1:
				d = cands[0]
				px = get_pos_x()
				py = get_pos_y()
				nx, ny = apply_direction(px, py, d)
				if nx == gx and ny == gy:
					QP("父机下一格宝", px, py, "->", nx, ny, "就地处理", "")
					move(d)
					continue
				QP("父机直进", dir_to_str(d), px, py, "->", nx, ny, "")
				move(d)
				visit_inc(edge_key(px, py, nx, ny))
				continue

			# 分叉：节点租约 + 限流 + 预算
			if not lease_try(cx, cy):
				# 节点被占：自己走主方向
				main_dir = cands[0]
				px = get_pos_x()
				py = get_pos_y()
				nx, ny = apply_direction(px, py, main_dir)
				if nx == gx and ny == gy:
					move(main_dir)
					continue
				move(main_dir)
				visit_inc(edge_key(px, py, nx, ny))
				continue

			main_dir = cands[0]
			others = []
			i = 1
			while i < len(cands):
				others.append(cands[i])
				i = i + 1

			budget = global_spawn_budget()
			fanout = MAX_FANOUT_PER_NODE
			if budget < fanout:
				fanout = budget
			if fanout < 0:
				fanout = 0

			children_dirs = []
			i = 0
			while i < len(others) and i < fanout:
				children_dirs.append(others[i])
				i = i + 1

			children = []
			k = 0
			while k < len(children_dirs):
				d = children_dirs[k]
				tx, ty = apply_direction(cx, cy, d)
				if can_expand_edge(cx, cy, tx, ty):
					claimed_add(cx, cy, tx, ty)

					def wrap(dcap, gxcap, gycap, born):
						def worker():
							return child_solver(dcap, gxcap, gycap, born)
						return worker

					h = None
					if ABORT_ALL == 0 and global_spawn_budget() > 0:
						h = spawn_drone(wrap(d, gx, gy, epoch_now()))
					if h:
						track_handle(h)
						children.append(h)
						QP("派子机(限流)", dir_to_str(d), "from", cx, cy, "kids", len(children), "")
					else:
						CLAIMED_EDGES.pop(edge_key(cx, cy, tx, ty))
				k = k + 1

			# 主方向自己走一步并计数
			px = get_pos_x()
			py = get_pos_y()
			nx, ny = apply_direction(px, py, main_dir)
			if nx == gx and ny == gy:
				QP("父机主路宝", px, py, "->", nx, ny, "就地处理", "")
				move(main_dir)
				lease_release(cx, cy)
				continue
			QP("父机主路", dir_to_str(main_dir), px, py, "->", nx, ny, "")
			move(main_dir)
			visit_inc(edge_key(px, py, nx, ny))

			# 非阻塞回收已结束的子机
			i2 = 0
			while i2 < len(children):
				if has_finished(children[i2]):
					res2 = wait_for(children[i2])
					children.pop(i2)
					if res2 != None and res2 != False:
						claimed_remove_path(res2[1])
						if res2[0] == "reused":
							QP("子机复用", "父机接管", "", "", "", "", "", "")
							wait_all_children_exit()
							memory_reset_after_reuse()
						elif res2[0] == "done":
							QP("子机收割", "父机结束轮", "", "", "", "", "", "")
							wait_all_children_exit()
							lease_release(cx, cy)
							return True
						else:
							# 合并访问计数
							visit_add_path(res2[1])
				else:
					i2 = i2 + 1
			lease_release(cx, cy)

# ---------------- 自适应启动 ----------------

def in_maze_now():
	return (measure() != None)

def main():
	quick_print("== 并行迷宫·复用300后收割·Trémaux+限流+租约+目标变更即退 ==", "", "", "", "", "", "", "")
	if num_unlocked(Unlocks.Costs) == 0:
		unlock(Unlocks.Costs)
	if num_unlocked(Unlocks.Mazes) == 0:
		unlock(Unlocks.Mazes)

	while True:
		reset_all_memory_for_new_round()
		global REUSE_COUNT
		global ACTIVE_HANDLES
		global ABORT_ALL
		REUSE_COUNT = 0
		ACTIVE_HANDLES = []
		ABORT_ALL = 0
		QP("新轮", "清空记忆", "VISITS", 0, "CLAIMED", 0, "", "")

		if not in_maze_now():
			QP("状态", "在迷宫外", "", "", "", "", "", "")
			if not ensure_single_bush_here():
				continue
			if not generate_initial_maze_once():
				continue
		else:
			if MAZE_COST <= 0:
				_set_maze_cost(compute_maze_cost())

		QP("状态", "在迷宫内", "", "", "", "", "", "")
		ok = parent_solve_maze_with_reuse()

		# 轮末：统一强制清场
		wait_all_children_exit()
		clear_abort()

# 入口
main()
