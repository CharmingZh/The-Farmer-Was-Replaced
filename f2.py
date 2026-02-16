# =================================================================
#  恐龙寻路AI v2.1 (兼容性修复)
#  - 目标：通过AI算法，让恐龙（贪吃蛇）尽可能多地吃苹果，增长尾巴。
#
#  - [v2.1 核心升级]
#  - 1. (兼容性修复): 修复了因单行内多重赋值导致的“左侧与右侧不匹配”的错误。
#  -    所有 `var1, var2 = ...` 的赋值操作均已拆分为多行，以确保最大兼容性。
# =================================================================

# ------------------ 辅助函数 ------------------

def get_next_pos(px, py, direction):
	if direction == North:
		return (px, py + 1)
	if direction == South:
		return (px, py - 1)
	if direction == East:
		return (px + 1, py)
	if direction == West:
		return (px - 1, py)
	return (px, py)

def is_safe(pos, tail, world_size):
	x, y = pos
	if x < 0 or x >= world_size or y < 0 or y >= world_size:
		return False
	# 检查时，不需要考虑最后一节尾巴
	i = 0
	while i < len(tail) - 1:
		if pos == tail[i]:
			return False
		i = i + 1
	return True

# ------------------ v2.0 核心算法 ------------------

def generate_hamiltonian_path(world_size):
	# 生成一个覆盖全图的“之”字形路径（非闭合环）
	# path_map 将存储每个点在路径中的下一个点
	path_map = {}
	y = 0
	while y < world_size:
		if y % 2 == 0: # 偶数行，从左到右
			x = 0
			while x < world_size - 1:
				path_map[(x, y)] = (x + 1, y)
				x = x + 1
			if y < world_size - 1:
				path_map[(x, y)] = (x, y + 1) # 行末向下
		else: # 奇数行，从右到左
			x = world_size - 1
			while x > 0:
				path_map[(x, y)] = (x - 1, y)
				x = x - 1
			if y < world_size - 1:
				path_map[(x, y)] = (x, y + 1) # 行末向下
		y = y + 1
	return path_map

def find_path_bfs(start_pos, target_pos, tail, world_size):
	# [v2.0] 使用列表重写BFS，确保兼容性
	queue = [(start_pos, [])]
	visited = [start_pos]

	while len(queue) > 0:
		current_pos, path = queue.pop(0)
		if current_pos == target_pos:
			return path

		possible_moves = [North, East, South, West]
		for direction in possible_moves:
			next_pos = get_next_pos(current_pos[0], current_pos[1], direction)
			
			# 检查 next_pos 是否已被访问
			is_visited = False
			for v_pos in visited:
				if v_pos == next_pos:
					is_visited = True
					break

			if not is_visited and is_safe(next_pos, tail, world_size):
				visited.append(next_pos)
				new_path = []
				for p_item in path:
					new_path.append(p_item)
				new_path.append(direction)
				queue.append((next_pos, new_path))
	return None

def get_best_move(target_x, target_y, tail, world_size, hamiltonian_path):
	px = get_pos_x()
	py = get_pos_y()
	head_pos = (px, py)
	target_pos = (target_x, target_y)

	# --- 智能模式：尝试寻找安全的苹果快捷方式 ---
	path_to_apple = find_path_bfs(head_pos, target_pos, tail, world_size)
	if path_to_apple:
		shortcut_move = path_to_apple[0]
		next_head_pos = get_next_pos(px, py, shortcut_move)
		
		# 安全检查：模拟走快捷方式后，看是否还能找到通往自己尾巴的路
		future_tail = [next_head_pos] + tail[:-1]
		path_to_tail = find_path_bfs(next_head_pos, future_tail[-1], future_tail, world_size)
		
		if path_to_tail:
			quick_print("AI_MODE: Smart - Taking shortcut to apple.")
			if move(shortcut_move):
				return True

	# --- 安全模式：如果快捷方式不安全或不存在，则沿预设路径移动 ---
	quick_print("AI_MODE: Safe - Following Hamiltonian Path.")
	next_safe_pos = hamiltonian_path.get(head_pos)
	
	# [v2.0 修复] 如果到达路径终点，则寻找回到起点的路
	if not next_safe_pos:
		quick_print("Path End Reached. Returning to start.")
		path_to_start = find_path_bfs(head_pos, (0,0), tail, world_size)
		if path_to_start:
			if move(path_to_start[0]):
				return True
		# 如果连回到起点的路都没有，说明被困
		return False # 被困住

	# 沿安全路径移动
	dx = next_safe_pos[0] - px
	dy = next_safe_pos[1] - py
	safe_direction = None
	if dx == 1:
		safe_direction = East
	if dx == -1:
		safe_direction = West
	if dy == 1:
		safe_direction = North
	if dy == -1:
		safe_direction = South

	if safe_direction:
		if move(safe_direction):
			return True

	return False

# ------------------ 主程序 ------------------

def main():
	world_size = 32
	set_world_size(world_size)
	
	# 生成安全路径
	hamiltonian_path = generate_hamiltonian_path(world_size)
	
	change_hat(Hats.Dinosaur_Hat)
	
	tail = []
	# [v2.1 修复] 将赋值拆分为两行
	px_start = get_pos_x()
	py_start = get_pos_y()
	
	next_apple_pos = measure()
	if not next_apple_pos:
		quick_print("错误: 无法在开始时测量到苹果位置!")
		change_hat(Hats.Gold_Hat)
		return
	target_x, target_y = next_apple_pos
	
	quick_print("开始游戏！第一个目标：", target_x, target_y)
	move(North)
	tail.append((px_start, py_start))
	
	while True:
		# [v2.1 修复] 将赋值拆分为多行
		last_pos_x = get_pos_x()
		last_pos_y = get_pos_y()
		last_pos = (last_pos_x, last_pos_y)
		
		if not get_best_move(target_x, target_y, tail, world_size, hamiltonian_path):
			quick_print("被困住了！游戏结束。")
			change_hat(Hats.Gold_Hat)
			quick_print("收获骨头数量：", len(tail) * len(tail))
			return
		
		tail.insert(0, last_pos)
		
		current_pos_x = get_pos_x()
		current_pos_y = get_pos_y()
		current_pos = (current_pos_x, current_pos_y)
		
		if current_pos == (target_x, target_y):
			# 吃到苹果，尾巴增长 (不移除末端)
			quick_print("到达苹果位置！尾巴长度：", len(tail))
			
			next_apple_pos = measure()
			if not next_apple_pos:
				quick_print("已吃完全部苹果或发生错误！即将收获。")
				change_hat(Hats.Gold_Hat)
				quick_print("收获骨头数量：", len(tail) * len(tail))
				return
			
			target_x, target_y = next_apple_pos
			quick_print("新目标：", target_x, target_y)
		else:
			# 未吃到苹果，尾巴移动 (移除末端)
			tail.pop()

main()

