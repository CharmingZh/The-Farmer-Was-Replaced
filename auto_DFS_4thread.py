# =================================================================
#
#   --- 全地图灌木种植 & 巨型迷宫一键生成 & 单机DFS（四无人机并行-两阶段版 v3） ---
#
#   思路：
#   - 阶段A（并行）：Q0 生成 Q1/Q2/Q3 三台无人机；四机分别在各自象限完成
#       1) ensure_bush_region（补植灌木）
#       2) wait_bush_mature_region（成熟检查）
#     子机完成后自动消失。Q0 用 num_drones()==1 作为“所有子机已完成”的屏障。
#   - 阶段B（单机）：只有 Q0 在 (0,0) 一次性 use_item(Items.Weird_Substance, n) 生成迷宫，
#     然后 solve_maze_dfs_once() 收宝。
#
#   关键保证：
#   - 只在 (0,0) 调用一次 use_item(Items.Weird_Substance, n)，杜绝 1×1 迷宫；
#   - 不使用 lambda/共享字典/全局并发变量；
#   - 同步完全依赖 num_drones()（所有子机退出后 == 1）。
#
# =================================================================

# -------------------- 通用/种植工具 --------------------

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
		x_start, x_end, x_step = (0, n, 1)
		if y % 2 != 0:
			x_start, x_end, x_step = (n - 1, -1, -1)
		x = x_start
		while x != x_end:
			move_to(x, y)
			if get_entity_type() == Entities.Grass and can_harvest():
				return (x, y)
			x = x + x_step
		y = y + 1
	return None

# 在 [x0..x1] × [y0..y1] 闭区间蛇形扫描，非灌木则补植为灌木
def ensure_bush_region(x0, y0, x1, y1):
	bush_cost = get_cost(Entities.Bush)
	if bush_cost == None:
		quick_print("错误：无法获取灌木成本。")
		return False
	yy = y0
	while yy <= y1:
		xs, xe, st = (x0, x1 + 1, 1)
		if (yy - y0) % 2 != 0:
			xs, xe, st = (x1, x0 - 1, -1)
		xx = xs
		while xx != xe:
			move_to(xx, yy)
			if get_entity_type() != Entities.Bush:
				# 资源补给（干草/木材）
				while (Items.Hay in bush_cost and num_items(Items.Hay) < bush_cost[Items.Hay]) or (Items.Wood in bush_cost and num_items(Items.Wood) < bush_cost[Items.Wood]):
					quick_print("资源不足，寻找可收割草...")
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

# 等待区域内全部灌木成熟
def wait_bush_mature_region(x0, y0, x1, y1):
	while True:
		all_m = True
		yy = y0
		while yy <= y1:
			xs, xe, st = (x0, x1 + 1, 1)
			if (yy - y0) % 2 != 0:
				xs, xe, st = (x1, x0 - 1, -1)
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
		quick_print("区域仍有未成熟灌木，继续等待...")

# -------------------- 迷宫一次性生成（仅 Q0 调用） --------------------

def generate_giant_maze_once():
	n = get_world_size()
	min_substance = n + n
	quick_print("检查 Weird_Substance，目标 ≥ ", min_substance, "。")
	while num_items(Items.Weird_Substance) < min_substance:
		quick_print("Weird_Substance 不足：", num_items(Items.Weird_Substance), "/", min_substance, "，等待产出...")
		return False
	move_to(0, 0)
	quick_print("一次性生成巨型迷宫：", n, "×", n, "...")
	use_item(Items.Weird_Substance, n)
	if measure() == None:
		quick_print("错误：use_item 后未检测到迷宫。")
		return False
	quick_print("巨型迷宫生成成功！")
	return True

# -------------------- DFS 解迷 --------------------

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

visited_cells = {}
treasure_location = None

def _visited_has(p):
	return (p in visited_cells)

def _visited_add(p):
	visited_cells[p] = True

def find_and_harvest_dfs(came_from = None):
	current = (get_pos_x(), get_pos_y())
	if treasure_location != None and current[0] == treasure_location[0] and current[1] == treasure_location[1]:
		quick_print("找到宝藏！收获中...")
		harvest()
		return True
	if _visited_has(current):
		return False
	_visited_add(current)
	directions = [North, East, South, West]
	i = 0
	while i < len(directions):
		d = directions[i]
		if d != came_from:
			if can_move(d):
				move(d)
				if find_and_harvest_dfs(get_opposite_direction(d)):
					return True
				# 回溯
				back = get_opposite_direction(d)
				if can_move(back):
					move(back)
		i = i + 1
	return False

def solve_maze_dfs_once():
	global treasure_location
	global visited_cells
	treasure_location = measure()
	if treasure_location == None:
		quick_print("错误：measure() 未返回迷宫坐标。")
		return False
	quick_print("宝藏位于(", treasure_location[0], ",", treasure_location[1], ")。启动 DFS...")
	visited_cells = {}
	ok = find_and_harvest_dfs()
	if ok:
		quick_print("DFS 成功收获宝藏 ✅")
		return True
	quick_print("DFS 失败：可达路径已穷尽。")
	return False

# -------------------- 象限划分与工人任务 --------------------

def get_quadrants():
	n = get_world_size()
	mid_x = (n - 1) // 2
	mid_y = (n - 1) // 2
	# Q0 左下、Q1 右下、Q2 左上、Q3 右上
	return {
		0: (0, 0, mid_x, mid_y),
		1: (mid_x + 1, 0, n - 1, mid_y),
		2: (0, mid_y + 1, mid_x, n - 1),
		3: (mid_x + 1, mid_y + 1, n - 1, n - 1)
	}

# 子无人机执行：本象限 补植→成熟检查，然后退出（spawn_drone 完成后会自动消失）
def quadrant_worker_once(qid):
	qmap = get_quadrants()
	x0 = qmap[qid][0]
	y0 = qmap[qid][1]
	x1 = qmap[qid][2]
	y1 = qmap[qid][3]
	quick_print("Q", qid, "：开始补植/成熟检查...")
	ensure_bush_region(x0, y0, x1, y1)
	wait_bush_mature_region(x0, y0, x1, y1)
	quick_print("Q", qid, "：本象限完成，退出。")

# -------------------- 启动器（两阶段并行） --------------------

def main():
	quick_print("== 四无人机两阶段并行版 启动 ==")

	# 可选解锁
	if num_unlocked(Unlocks.Costs) == 0:
		unlock(Unlocks.Costs)
	if num_unlocked(Unlocks.Mazes) == 0:
		unlock(Unlocks.Mazes)

	while True:
		# --- 阶段A：并行完成四象限 补植+成熟 ---
		qmap = get_quadrants()

		# 显式定义三个子函数（避免 lambda）
		def worker_Q1():
			quadrant_worker_once(1)
		def worker_Q2():
			quadrant_worker_once(2)
		def worker_Q3():
			quadrant_worker_once(3)

		# 启动三台子无人机
		if num_drones() < max_drones():
			spawn_drone(worker_Q1)
		if num_drones() < max_drones():
			spawn_drone(worker_Q2)
		if num_drones() < max_drones():
			spawn_drone(worker_Q3)

		# 主无人机负责 Q0
		quadrant_worker_once(0)

		# 等待全部子无人机自动结束（num_drones() 回到 1）
		while num_drones() > 1:
			# 空转等待；也可在此做一些轻量维护
			pass

		# --- 阶段B：单机生成迷宫 + DFS 收宝 ---
		if not generate_giant_maze_once():
			quick_print("资源不足，下一轮重试迷宫生成。")
			continue

		if not solve_maze_dfs_once():
			quick_print("DFS 未成功，下一轮重试。")

		# 回到农场后自动进入下一轮循环

# -------------------- 脚本入口 --------------------
main()
