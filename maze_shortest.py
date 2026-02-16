# =================================================================
#
#   --- 智能勘探寻路算法 (v4) ---
#
#   此脚本通过模拟真实探险家的行为来解决迷宫，确保100%成功率。
#
#   工作流程:
#   1. 智能勘探: 无人机从起点出发，通过“前进-探索-回溯”的方式，
#      亲自走遍所有可达路径，在内存中绘制出精确的迷宫地图。
#      这从根本上解决了之前版本无法处理墙壁的问题。
#   2. 内存寻路: 在精确地图的基础上，瞬间计算出通往宝藏的路径。
#   3. 精准执行: 沿着计算出的无障碍路径，直达终点。
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

# --- 全局变量，用于在勘探过程中共享状态 ---
maze_map = {}
visited_for_exploration = set()

# --- 核心勘探与寻路逻辑 ---

def explore_and_map_maze(x, y):
	# 阶段一：通过递归深度优先搜索，智能勘探迷宫并绘制地图。
	# 无人机当前必须实际位于 (x, y) 坐标。
	
	visited_for_exploration.add((x, y))
	
	exits = []
	all_directions = [(North, 0, 1), (East, 1, 0), (South, 0, -1), (West, -1, 0)]
	
	for direction_cmd, dx, dy in all_directions:
		if can_move(direction_cmd):
			exits.append(direction_cmd)
			next_pos = (x + dx, y + dy)
			if not (next_pos in visited_for_exploration):
				# 1. 前进
				move(direction_cmd)
				# 2. 从新位置递归勘探
				explore_and_map_maze(next_pos[0], next_pos[1])
				# 3. 回溯 (关键步骤)
				move(get_opposite_direction(direction_cmd))
	
	# 记录当前位置的所有有效出口
	maze_map[(x, y)] = exits

def solve_maze_with_exploration():
	quick_print("进入迷宫，启动智能勘探寻路算法...")
	
	treasure_pos = measure()
	if treasure_pos == None:
		quick_print("错误：measure() 函数未能返回迷宫内的坐标！")
		return False
	
	start_pos = (get_pos_x(), get_pos_y())
	
	if start_pos[0] == treasure_pos[0] and start_pos[1] == treasure_pos[1]:
		quick_print("起点就是宝藏，立即收获。")
		harvest()
		return True
		
	# --- 阶段一：智能勘探 ---
	quick_print("阶段一：开始智能勘探，绘制精确地图...")
	explore_and_map_maze(start_pos[0], start_pos[1])
	quick_print("地图绘制完成！")
	
	# --- 阶段二：在内存中计算路径 ---
	quick_print("阶段二：在内存中快速计算路径...")
	stack = [(start_pos, [])]
	visited_for_pathfinding = {start_pos: True}
	path_to_treasure = None
	dir_to_delta = { North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0) }

	while len(stack) > 0:
		current_pos, path = stack.pop()
		cx, cy = current_pos

		if current_pos[0] == treasure_pos[0] and current_pos[1] == treasure_pos[1]:
			path_to_treasure = path
			break

		if current_pos in maze_map:
			for direction_cmd in maze_map[current_pos]:
				dx, dy = dir_to_delta[direction_cmd]
				next_pos = (cx + dx, cy + dy)
				if not (next_pos in visited_for_pathfinding):
					visited_for_pathfinding[next_pos] = True
					new_path = list(path)
					new_path.append(direction_cmd)
					stack.append((next_pos, new_path))
	
	# --- 阶段三：执行计算出的路径 ---
	if path_to_treasure != None:
		quick_print("阶段三：路径计算完毕，长度为:", len(path_to_treasure), "步。现在开始执行...")
		# 勘探结束后，无人机已自动回溯至起点，可以直接执行路径
		for move_cmd in path_to_treasure:
			move(move_cmd)
		
		quick_print("已到达宝藏位置，正在收获！")
		harvest()
		return True
	else:
		quick_print("错误：计算路径失败，迷宫可能无解。")
		return False

# --- 脚本入口 ---
solve_maze_with_exploration()

