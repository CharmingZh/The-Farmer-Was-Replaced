# =================================================================
#  并行刷迷宫 · 子机优先复用/收割 + 轮次(EPOCH)抢占版
#
#  V12 修正:
#  - 修复：[根本] V11 的探索逻辑 (父/子机同时DFS) 存在根本缺陷。
#  - 机制：重构回“主-从”逻辑。
#  - 修复：child_solver 被极大简化，现在只执行 sprint_or_branch（冲刺）。
#    它不再执行 DFS，也绝不派发新子机。
#  - 修复：parent_solve_to_treasure 是唯一的 DFS 线程。
#    它派发 child_solver 作为“冲刺探测器”。
#  - 机制：父机不再调用 child_solver 替自己跑图，而是自己 move() 并 continue 循环。
#  - 结果：这修复了 V11 日志中因逻辑混乱导致的探索过早失败。
# =================================================================

DEBUG = 1

def QP(a, b, c, d, e, f, g, h):
	if DEBUG == 1:
		quick_print(a, b, c, d, e, f, g, h)

# ------------------ 全局状态 ------------------

EXPLORED_EDGES = {}
CLAIMED_EDGES = {}
CHILDREN = []

TREASURE_LOCK = 0
RELOC = 0
MAX_RELOC = 300

# V11 状态：灌木位置记忆
BUSH_POS_X = -1
BUSH_POS_Y = -1

# 轮次控制：每次“进入新迷宫”或“复用成功”都应视为新一轮
EPOCH = 0
CANCEL_FLAG = 0

# ------------------ 工具方法 ------------------

def maze_weird_amount():
	size = get_world_size()
	lv = num_unlocked(Unlocks.Mazes)
	if lv < 1:
		lv = 1
	return size * (2 ** (lv - 1))

def try_lock_treasure():
	global TREASURE_LOCK
	if TREASURE_LOCK == 0:
		TREASURE_LOCK = 1
		return True
	return False

def release_treasure():
	global TREASURE_LOCK
	TREASURE_LOCK = 0

def reset_memory():
	global EXPLORED_EDGES
	global CLAIMED_EDGES
	EXPLORED_EDGES = {}
	CLAIMED_EDGES = {}

def bump_epoch():
	global EPOCH
	global CANCEL_FLAG
	EPOCH = EPOCH + 1
	CANCEL_FLAG = 0

def mark_cancel():
	global CANCEL_FLAG
	CANCEL_FLAG = 1

def edge_key(ax, ay, bx, by):
	if ax < bx:
		return ((ax, ay), (bx, by))
	if ax > bx:
		return ((bx, by), (ax, ay))
	if ay <= by:
		return ((ax, ay), (bx, by))
	return ((bx, by), (ax, ay))

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

def in_maze_now():
	return measure() != None

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

# V11 移植
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

def can_probe(x, y, d):
	cx = get_pos_x()
	cy = get_pos_y()
	if x == cx and y == cy:
		return can_move(d)
	return False

def clearance_score(cx, cy, d):
	if not can_move(d):
		return -9999
	nx, ny = apply_direction(cx, cy, d)
	back = get_opposite_direction(d)
	dirs = [North, East, South, West]
	cnt = 0
	i = 0
	while i < len(dirs):
		dd = dirs[i]
		if dd != back and can_probe(nx, ny, dd):
			cnt = cnt + 1
		i = i + 1
	side_penalty = 0
	if d == North or d == South:
		if (not can_probe(cx, cy, East)) and (not can_probe(cx, cy, West)):
			side_penalty = 1
	if d == East or d == West:
		if (not can_probe(cx, cy, North)) and (not can_probe(cx, cy, South)):
			side_penalty = 1
	return cnt - side_penalty

# ------------------ 造迷宫 ------------------

def ensure_single_bush_here():
	if get_entity_type() != Entities.Bush:
		if get_ground_type() != Grounds.Soil:
			till()
		ok = plant(Entities.Bush)
		if not ok:
			QP("错误", "灌木种植失败", "", "", "", "", "", "")
			return False
	return True

def generate_giant_maze_once():
	global BUSH_POS_X
	global BUSH_POS_Y # V11
	
	need = maze_weird_amount()
	cur = num_items(Items.Weird_Substance)
	QP("检查Weird", "需≥", need, "现有", cur, "", "", "")
	if cur < need:
		QP("Weird不足", cur, "/", need, "", "", "", "")
		return False
	if not ensure_single_bush_here():
		return False
	
	BUSH_POS_X = get_pos_x()
	BUSH_POS_Y = get_pos_y()
	
	ok = use_item(Items.Weird_Substance, need)
	if not ok:
		QP("错误", "use_item失败", "", "", "", "", "", "")
		BUSH_POS_X = -1 # V11: 失败重置
		BUSH_POS_Y = -1
		return False
	if measure() == None:
		QP("错误", "迷宫生成失败", "", "", "", "", "", "")
		BUSH_POS_X = -1 # V11: 失败重置
		BUSH_POS_Y = -1
		return False
	QP("迷宫生成成功", "at", BUSH_POS_X, BUSH_POS_Y, "amt", need, "", "")
	return True

# ------------------ V12 子机：简化为“冲刺者” ------------------
# 它不再执行 DFS，不再派发子机

def child_solver(initial_dir, gx, gy, my_epoch):
	global BUSH_POS_X
	global BUSH_POS_Y
	
	if measure() == None:
		return ("abort", [])
	
	# V12：子机只保留 sprint_or_branch 逻辑
	# 它不再需要 explored_local 或 claimed_local
	
	def should_abort_epoch():
		return (CANCEL_FLAG == 1) or (my_epoch != EPOCH) or (measure() == None)

	# --- V12: `sprint_or_branch` 现在是 `child_solver` 的主体 ---
	local_path = []
	if initial_dir == None:
		return ("deadend", local_path)
		
	d = initial_dir
	while True:
		if should_abort_epoch():
			return ("stale", local_path)
			
		if not can_move(d):
			return ("deadend", local_path)
			
		px = get_pos_x()
		py = get_pos_y()
		nx, ny = apply_direction(px, py, d)
		ek = edge_key(px, py, nx, ny)
		
		# 命中宝藏
		if nx == gx and ny == gy:
			move(d)
			local_path.append(ek)
			need0 = maze_weird_amount()
			if try_lock_treasure():
				if RELOC < MAX_RELOC and num_items(Items.Weird_Substance) >= need0:
					ok0 = use_item(Items.Weird_Substance, need0)
					if ok0:
						mark_cancel()
						BUSH_POS_X = get_pos_x() # V11: 更新灌木位置
						BUSH_POS_Y = get_pos_y()
						release_treasure()
						return ("reused", local_path)
				harvest()
				mark_cancel()
				BUSH_POS_X = -1 # V11: 收割，重置灌木位置
				BUSH_POS_Y = -1
				release_treasure()
				return ("harvested", local_path)
			else:
				# 锁被别人占了，当做普通胜利，让父机处理
				return ("win", local_path)
				
		move(d)
		local_path.append(ek)
		
		if should_abort_epoch():
			return ("stale", local_path)
			
		cx0 = get_pos_x()
		cy0 = get_pos_y()
		back = get_opposite_direction(d)
		dirs0 = [North, East, South, West]
		
		# V12: 子机只关心“单行道”还是“分叉/死路”
		cands_count = 0
		next_dir = None
		i0 = 0
		while i0 < len(dirs0):
			dd = dirs0[i0]
			if dd != back and can_move(dd):
				cands_count = cands_count + 1
				next_dir = dd
			i0 = i0 + 1
			
		if cands_count == 1:
			# 单行道，继续冲刺
			d = next_dir
			continue
			
		# cands_count == 0 (死路)
		# cands_count > 1 (分叉)
		# 无论哪种，冲刺结束，返回给父机
		return ("deadend", local_path)
		
	# --- V12: 删除了 V11 中 child_solver 的 DFS (while True) 循环 ---

# ------------------ V12 父机：唯一的 DFS 探索者 ------------------

def parent_solve_to_treasure():
	g = measure()
	if g == None:
		QP("错误", "无迷宫", "", "", "", "", "", "")
		return False
	gx = g[0]
	gy = g[1]
	my_epoch = EPOCH

	while True:
		# 本轮被取消或迷宫消失则退出，让主循环接管
		if (my_epoch != EPOCH) or (measure() == None) or (CANCEL_FLAG == 1):
			return ("stale", [])

		cx = get_pos_x()
		cy = get_pos_y()
		if cx == gx and cy == gy:
			QP("父机到达", "宝箱处", cx, cy, "E", my_epoch, "", "")
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

		# --- V12 修正的等待/探索逻辑 ---
		if len(cands) == 0:
			# V10/V11 的等待逻辑是正确的
			if len(CHILDREN) == 0:
				QP("父机被困", "无路可走", "也无子机", cx, cy, "E", my_epoch, "")
				return False # 真正被困
			
			QP("父机无路", "等待子机", cx, cy, "孩子", len(CHILDREN), "E", my_epoch)
			iw = 0
			has_processed_child_this_tick = False
			
			while iw < len(CHILDREN):
				if has_finished(CHILDREN[iw]):
					has_processed_child_this_tick = True
					resw = wait_for(CHILDREN[iw])
					CHILDREN.pop(iw) # 无论结果如何都弹出
					
					if resw != None and resw != False:
						status_w = resw[0]
						path_w = resw[1]
						
						if status_w == "reused" or status_w == "harvested":
							return resw # 成功，退出
						if status_w == "win":
							return True # 成功，退出
						
						# V12: 子机返回的路径都是需要合并的
						if status_w == "deadend" or status_w == "stale" or status_w == "abort":
							explored_add_path(path_w)
							claimed_remove_path(path_w)
							
					iw = 0 
					continue
				iw = iw + 1
			
			if len(CHILDREN) == 0 and has_processed_child_this_tick:
				QP("父机被困", "所有子机失败", "cands=0", cx, cy, "E", my_epoch, "")
				return False # 真正被困
				
			continue # V10/V11 修正：继续等待
		# --- V10/V11 等待逻辑结束 ---

		# --- V12 探索逻辑 ---
		best_dir = None
		best_sc = -9999
		i2 = 0
		while i2 < len(cands):
			d = cands[i2]
			sc = clearance_score(cx, cy, d)
			if sc > best_sc:
				best_sc = sc
				best_dir = d
			i2 = i2 + 1
		
		# V12: 派发子机 (冲刺者)
		i3 = 0
		while i3 < len(cands):
			d = cands[i3]
			if d != best_dir:
				tx2, ty2 = apply_direction(cx, cy, d)
				claimed_add(cx, cy, tx2, ty2) # 标记此路已被子机“认领”
				def wrap2(dcap, gxcap, gycap, epcap):
					def worker():
						return child_solver(dcap, gxcap, gycap, epcap)
					return worker
				h = spawn_drone(wrap2(d, gx, gy, my_epoch))
				if h:
					CHILDREN.append(h)
			i3 = i3 + 1

		# V12: 父机自己走 best_dir，并继续 DFS 循环
		nx, ny = apply_direction(cx, cy, best_dir)
		ek = edge_key(cx, cy, nx, ny)
		
		# 父机将亲自探索这条路，立即将其标记为“已探索”
		explored_add_path([ek]) 
		move(best_dir)
		
		# V12: 删除了 `status, pth = child_solver(...)` 的错误调用
		# 父机通过 continue 继续主循环，从新位置 (nx, ny) 开始 DFS
		continue 

# ------------------ 主循环：生成 → 多轮寻宝 → 复用/收割 → 提升 EPOCH ------------------

def multi_thread_maze_farming():
	global RELOC
	global MAX_RELOC
	global EPOCH
	global BUSH_POS_X
	global BUSH_POS_Y # V11

	RELOC = 0
	MAX_RELOC = 300
	EPOCH = 0
	CANCEL_FLAG = 0
	BUSH_POS_X = -1 # V11
	BUSH_POS_Y = -1

	if in_maze_now():
		QP("警告", "在迷宫中启动", "无法定位灌木", "将尝试收割重置", "", "", "", "")
		harvest()
		if in_maze_now():
			QP("致命", "无法收割", "请手动重置", "", "", "", "", "")
			return

	while True:
		if not in_maze_now():
			QP("状态", "迷宫外", "准备生成", "E", EPOCH, "", "", "")
			okg = generate_giant_maze_once()
			if not okg:
				return 
			bump_epoch()
		
		if BUSH_POS_X == -1 and in_maze_now():
			QP("状态", "迷宫内", "但BUSH_POS未知", "E", EPOCH, "", "", "")
			harvest()
			if in_maze_now():
				QP("致命", "无法重置迷宫", "退出", "", "", "", "", "")
				return
			continue 

		QP("状态", "迷宫内", "BUSH_AT", BUSH_POS_X, BUSH_POS_Y, "E", EPOCH, "")
		res = parent_solve_to_treasure()
		
		# --- V11 失败处理 ---
		if res == False:
			QP("失败/中断", "父机被困", "尝试重置", BUSH_POS_X, BUSH_POS_Y, "E", EPOCH, "")
			if BUSH_POS_X == -1:
				QP("致命", "灌木位置未知", "无法重置", "", "", "", "", "")
				return 
			
			move_to(BUSH_POS_X, BUSH_POS_Y)
			harvest()
			
			if in_maze_now():
				QP("致命", "Harvest失败", "迷宫仍存在", "", "", "", "", "")
				return 
				
			QP("...", "迷宫已重置", "将生成新迷宫", "", "", "", "", "")
			BUSH_POS_X = -1 
			BUSH_POS_Y = -1
			RELOC = 0 
			reset_memory() 
			continue
		# --- V11 失败处理结束 ---

		kind = "reach"
		if res != True and res != False:
			kind = res[0]

		# V12: 增加对 "stale" 的处理
		if kind == "stale":
			if CANCEL_FLAG == 1:
				QP("父机 STALE", "因 CANCEL_FLAG", "等待子机结果", "E", EPOCH, "", "", "")
				# 一个子机赢了，但父机先收到了 STALE 信号。
				# 我们什么都不做，继续循环。
				# 下一轮 in_maze_now() 仍为 true, 
				# parent_solve 会在顶部检查 CANCEL_FLAG 并立即返回 "stale"
				# ...
				# V12.1 修正：我们必须等待所有子机结束
				iw_s = 0
				while iw_s < len(CHILDREN):
					if has_finished(CHILDREN[iw_s]):
						res_s = wait_for(CHILDREN[iw_s])
						CHILDREN.pop(iw_s)
						if res_s != None and res_s != False:
							if res_s[0] == "reused" or res_s[0] == "harvested":
								kind = res_s[0] # 找到了真正的胜利者
								break
					else:
						# 如果还有子机没跑完，我们不能 bump epoch
						# V12.2 修正: 应该强制等待
						wait_for(CHILDREN[iw_s])
						CHILDREN.pop(iw_s)
					iw_s = 0 # 重置
			else:
				# 迷宫消失了，但不是因为 CANCEL
				QP("父机 STALE", "迷宫消失?", "视为失败", "E", EPOCH, "", "", "")
				# 强制走失败逻辑
				move_to(BUSH_POS_X, BUSH_POS_Y)
				harvest()
				if in_maze_now():
					QP("致命", "Harvest失败", "迷宫仍存在", "", "", "", "", "")
					return
				BUSH_POS_X = -1 
				BUSH_POS_Y = -1
				RELOC = 0 
				reset_memory() 
				continue

		if kind == "reused":
			QP("复用成功", "第", RELOC + 1, "次", "提升E", EPOCH + 1, "", "")
			RELOC = RELOC + 1
			reset_memory()
			bump_epoch()
			continue

		if kind == "harvested":
			QP("收割结束", "reloc", RELOC, "/", MAX_RELOC, "E", EPOCH, "", "")
			return

		# (kind == "reach" or kind == "win")
		# 父机自己到宝箱但未处理 → 尝试本格复用，否则收割
		need = maze_weird_amount()
		if RELOC < MAX_RELOC and num_items(Items.Weird_Substance) >= need:
			if try_lock_treasure():
				okx = use_item(Items.Weird_Substance, need)
				if okx:
					QP("复用成功", "第", RELOC + 1, "次", "提升E", EPOCH + 1, "", "")
					RELOC = RELOC + 1
					BUSH_POS_X = get_pos_x() # V11: 父机复用，更新位置
					BUSH_POS_Y = get_pos_y()
					reset_memory()
					mark_cancel()
					release_treasure()
					bump_epoch()
					continue
				release_treasure()

		if try_lock_treasure():
			QP("收割宝箱", "reloc", RELOC, "/", MAX_RELOC, "E", EPOCH, "", "")
			harvest()
			BUSH_POS_X = -1 # V11: 父机收割，重置位置
			BUSH_POS_Y = -1
			mark_cancel()
			release_treasure()
		return

# ------------------ 入口 ------------------

def main():
	if num_unlocked(Unlocks.Mazes) == 0:
		unlock(Unlocks.Mazes)
	set_execution_speed(0)
	multi_thread_maze_farming()

main()