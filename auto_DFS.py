# =================================================================
#
#   --- 全地图灌木种植 & 巨型迷宫一键生成 & DFS解迷 监督器 (v1) ---
#
#   流程（循环往复）：
#   1) 蛇形扫描 → 非灌木则种灌木（缺料自动找草收割补足）
#   2) 等待全图灌木成熟
#   3) 一次性 use_item(Items.Weird_Substance, n) 生成 n×n 巨型迷宫
#   4) 直接探索式 DFS 寻路，找到宝藏立刻收获
#   5) 回到农场后，进入下一轮（因迷宫清场导致有“非灌木”格，会再次补种）
#
#   关键修复：
#   - 只在一棵格子上调用一次 use_item(Items.Weird_Substance, n)；
#     不再逐格调用，避免 1×1 迷宫。
#
# =================================================================

# -------------------- 通用/种植部分（继承你的 maze.py 思路） --------------------

def move_to(tx, ty):
	# 高效地移动到目标坐标。
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
	# 扫描全图寻找可收割的草（蛇形）。找到即返回坐标。
	# 注意：此函数会移动无人机，并停留在扫描到的位置。
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

def ensure_full_bush_coverage():
	# 蛇形扫描全图；若不是灌木，则检查资源→补充→种灌木。
	n = get_world_size()
	bush_cost = get_cost(Entities.Bush)
	if bush_cost == None:
		quick_print("错误：无法获取灌木成本，停止。")
		return False

	quick_print("开始全图蛇形扫描与补植...")
	y = 0
	while y < n:
		x_start, x_end, x_step = (0, n, 1)
		if y % 2 != 0:
			x_start, x_end, x_step = (n - 1, -1, -1)
		x = x_start
		while x != x_end:
			move_to(x, y)
			if get_entity_type() != Entities.Bush:
				quick_print("地块(", x, ",", y, ") 非灌木，准备种植。")
				# 资源检查与补给（干草/木材）
				while (Items.Hay in bush_cost and num_items(Items.Hay) < bush_cost[Items.Hay]) or (Items.Wood in bush_cost and num_items(Items.Wood) < bush_cost[Items.Wood]):
					quick_print("资源不足（需要干草/木材）。开始全图寻找可收割草...")
					grass_pos = find_harvestable_grass()
					if grass_pos != None:
						# 已在草地上
						harvest()
						quick_print("已收割草，返回种植点继续。")
						move_to(x, y)
					else:
						quick_print("没有找到可收割草，返回原位等待生长。")
						move_to(x, y)
						# 等待下一次循环再尝试
						pass
				# clear() 若你的版本要求先清理，可以解开下一行
				# clear()
				plant(Entities.Bush)
				quick_print("成功种植灌木于(", x, ",", y, ")。")
			x = x + x_step
		y = y + 1
	quick_print("全图补植完成。")
	return True

def wait_all_bush_mature():
	# 等待直至全图灌木 mature（可收获）
	n = get_world_size()
	quick_print("等待所有灌木成熟中...")
	while True:
		is_fully_mature = True
		y_check = 0
		while y_check < n:
			x_s, x_e, x_st = (0, n, 1)
			if y_check % 2 != 0:
				x_s, x_e, x_st = (n - 1, -1, -1)
			x_check = x_s
			while x_check != x_e:
				move_to(x_check, y_check)
				if get_entity_type() == Entities.Bush and not can_harvest():
					is_fully_mature = False
					break
				x_check = x_check + x_st
			if not is_fully_mature:
				break
			y_check = y_check + 1
		if is_fully_mature:
			quick_print("全部成熟 ✅")
			return
		quick_print("仍有未成熟灌木，继续等待...")

def generate_giant_maze_once():
	# 保证资源→一次性生成 n×n 巨型迷宫
	n = get_world_size()
	min_substance = n + n
	quick_print("准备生成迷宫，检查 Weird Substance...")
	while num_items(Items.Weird_Substance) < min_substance:
		quick_print("Weird Substance 不足。需要:", min_substance, "当前:", num_items(Items.Weird_Substance), "。等待补给/产出中...")
		# 等待下一循环检查

	# 选择一个稳定入口位置（角落 0,0），或你也可改为寻找一棵成熟灌木作为入口
	move_to(0, 0)
	quick_print("资源充足，开始一次性生成", n, "×", n, "巨型迷宫...")
	use_item(Items.Weird_Substance, n)

	# 确认已进入迷宫维度
	if measure() == None:
		quick_print("错误：use_item 后未检测到迷宫。")
		return False
	quick_print("巨型迷宫生成成功！")
	return True

# -------------------- DFS 解迷部分（继承你的 dfs.py 思路） --------------------

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

# 用“列表/映射”模拟集合，保持与自创语言一致的风格
visited_cells = {}
treasure_location = None

def _visited_has(p):
	return (p in visited_cells)

def _visited_add(p):
	visited_cells[p] = True

def find_and_harvest_dfs(came_from = None):
	# 递归探索 + 回溯；发现宝藏立即收获并返回 True
	current = (get_pos_x(), get_pos_y())

	# 优先检查是否到达宝藏
	if current[0] == treasure_location[0] and current[1] == treasure_location[1]:
		quick_print("找到宝藏！正在收获...")
		harvest()
		return True

	# 防重复
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
				move(get_opposite_direction(d))
		i = i + 1

	return False

def solve_maze_dfs():
	# 外层包装：读取宝藏坐标、清空访问集并发起 DFS
	quick_print("启动直接探索式 DFS...")
	global treasure_location
	treasure_location = measure()
	if treasure_location == None:
		quick_print("错误：measure() 未返回迷宫内坐标！")
		return False

	# 清空访问记录
	global visited_cells
	visited_cells = {}

	quick_print("宝藏位于(", treasure_location[0], ",", treasure_location[1], ")。开始探索...")
	ok = find_and_harvest_dfs()
	if ok:
		quick_print("DFS 成功收获宝藏 ✅")
		return True
	quick_print("错误：所有可达路径均探索，未能到达宝藏。")
	return False

# -------------------- 监督器：自动交替执行 --------------------

def supervisor_loop():
	quick_print("== 自动监督器 启动 ==")

	# 可选：确保必要解锁到位（如果你的存档需要）
	if num_unlocked(Unlocks.Costs) == 0:
		unlock(Unlocks.Costs)
	if num_unlocked(Unlocks.Mazes) == 0:
		unlock(Unlocks.Mazes)

	# 主循环：农场维度 → 迷宫维度 → 农场维度 → ...
	while True:
		quick_print("---- 新一轮开始：全图补植 → 等待成熟 ----")
		if not ensure_full_bush_coverage():
			quick_print("补植失败，下一轮重试。")
			continue

		wait_all_bush_mature()

		quick_print("---- 生成巨型迷宫 ----")
		if not generate_giant_maze_once():
			quick_print("生成迷宫失败，回农场后下一轮重试。")
			continue

		quick_print("---- 进入 DFS 解迷 ----")
		if not solve_maze_dfs():
			quick_print("DFS 失败，可能是异常迷宫；返回农场后重试。")

		quick_print("---- 本轮结束：应当已回到农场。下一轮即将开始。 ----")

# -------------------- 脚本入口 --------------------
supervisor_loop()
