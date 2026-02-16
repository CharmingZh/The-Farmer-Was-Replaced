# =================================================================
#
#   --- 直接探索式寻路算法 (v7 - 流畅移动版) ---
#
#   此脚本采用经典的深度优先搜索（DFS）策略，直接在迷宫中进行探索。
#   它的行为就像一个探险家，沿着一条路走到黑，遇到死路再返回尝试
#   其他分支。
#
#   核心优势:
#   - 效率极高: 它将探索和寻路合二为一。
#   - 立即行动: 一旦发现宝藏，会立刻停止探索并进行收获。
#   - 流畅移动: 优化了探索逻辑，避免了不必要的回头尝试，
#     移除了移动中的“抖动”现象。
#
# =================================================================

# --- 辅助函数 ---

def get_opposite_direction(direction):
	# 返回给定方向的相反方向，用于回溯。
	if direction == North:
		return South
	if direction == South:
		return North
	if direction == East:
		return West
	if direction == West:
		return East
	return None

# --- 全局变量 ---
visited = set() # 用于记录已访问过的坐标，防止无限循环。
treasure_location = None # 用于存储宝藏的坐标。

# --- 核心递归寻路函数 ---

def find_and_harvest_dfs(came_from=None):
	# 这是一个递归函数，它会移动无人机进行探索。
	# 新增 `came_from` 参数，用于避免不必要的回头探索。
	# 如果找到了宝藏，它会返回 True；如果是死路，则返回 False。
	
	current_pos = (get_pos_x(), get_pos_y())
	
	# 优先检查是否找到宝藏
	if current_pos[0] == treasure_location[0] and current_pos[1] == treasure_location[1]:
		quick_print("找到宝藏！正在收获...")
		harvest()
		return True

	# 检查是否已访问过
	if current_pos in visited:
		return False
	visited.add(current_pos)

	# 探索所有可行的方向
	all_directions = [North, East, South, West]
	for direction in all_directions:
		# --- 优化点: 如果这个方向是回头路，则跳过 ---
		if direction == came_from:
			continue

		if can_move(direction):
			move(direction)
			# 从新位置继续递归探索，并告诉下一层它是从哪个方向来的
			if find_and_harvest_dfs(get_opposite_direction(direction)):
				return True # 如果子路径找到了宝藏，直接返回成功
			
			# 如果子路径是死路，则回溯到当前位置
			move(get_opposite_direction(direction))
	
	# 如果所有方向都尝试过且都是死路，则返回失败
	return False

# --- 脚本主入口 ---

def solve_maze_directly():
	quick_print("启动直接探索式寻路算法...")
	
	global treasure_location
	treasure_location = measure()
	
	if treasure_location == None:
		quick_print("错误：measure() 函数未能返回迷宫内的坐标！")
		return
	
	quick_print("宝藏位于:", treasure_location[0], ",", treasure_location[1], "。开始探索...")
	
	# 初始调用时，没有“来自”的方向
	if find_and_harvest_dfs():
		quick_print("任务成功完成！")
	else:
		quick_print("错误：探索了所有可达路径，但未能找到宝藏。")

# --- 开始执行 ---
solve_maze_directly()

