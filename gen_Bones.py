# =================================================================
#  恐龙寻路AI v1.4 (终极修复版)
#  - 目标：通过AI算法，让恐龙（贪吃蛇）尽可能多地吃苹果，增长尾巴。
#
#  - [v1.4 修复与优化]
#  - 1. (终极修复): 将 `== None` 的检查升级为更通用的 `if not ...` 检查。
#  -    这可以正确处理 measure() 返回的 None, 0, False 或空列表等所有无效情况，
#  -    彻底解决程序崩溃问题。
#  - 2. (采纳修改): 继续使用你更正的 Hats.Gold_Hat。
# =================================================================

# ------------------ 辅助函数 ------------------

def get_next_pos(px, py, direction):
	# 计算给定方向的下一个坐标（不考虑环面）
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
	# 检查一个位置是否安全（在边界内且不是尾巴）
	x, y = pos
	if x < 0 or x >= world_size or y < 0 or y >= world_size:
		return False
	if pos in tail:
		return False
	return True

# ------------------ 核心AI移动逻辑 ------------------

def make_smart_move(target_x, target_y, tail, world_size):
	# 智能移动函数：优先向目标移动，同时避开尾巴
	px = get_pos_x()
	py = get_pos_y()
	
	dx = target_x - px
	dy = target_y - py
	
	# 根据距离目标的远近，建立移动方向的优先级列表
	preferred_moves = []
	if abs(dx) > abs(dy):
		# 优先左右移动
		if dx > 0:
			preferred_moves.append(East)
		if dx < 0:
			preferred_moves.append(West)
		if dy > 0:
			preferred_moves.append(North)
		if dy < 0:
			preferred_moves.append(South)
	else:
		# 优先上下移动
		if dy > 0:
			preferred_moves.append(North)
		if dy < 0:
			preferred_moves.append(South)
		if dx > 0:
			preferred_moves.append(East)
		if dx < 0:
			preferred_moves.append(West)
		
	# 尝试按优先级移动
	for direction in preferred_moves:
		next_pos = get_next_pos(px, py, direction)
		if is_safe(next_pos, tail, world_size):
			if move(direction):
				return True # 移动成功

	# 如果所有优先方向都失败了，尝试任意一个安全的方向（用于逃生）
	all_moves = [North, East, South, West]
	for direction in all_moves:
		if direction not in preferred_moves:
			next_pos = get_next_pos(px, py, direction)
			if is_safe(next_pos, tail, world_size):
				if move(direction):
					return True # 移动成功
	
	# 如果所有方向都无法移动，则被困住
	return False

# ------------------ 主程序 ------------------

def main():
	# 将世界设置为一个更具挑战的大小
	world_size = 32
	set_world_size(world_size)
	
	# 装备恐龙帽，开始游戏
	change_hat(Hats.Dinosaur_Hat)
	
	# 初始化尾巴列表和当前位置
	tail = []
	px, py = get_pos_x(), get_pos_y()
	
	# [v1.4 修复] 使用更健壮的检查来安全地测量第一个苹果
	next_apple_pos = measure()
	if not next_apple_pos: # 这个检查可以捕获 None, 0, False, 空列表/元组等所有无效情况
		quick_print("错误: 无法在开始时测量到苹果位置!")
		change_hat(Hats.Gold_Hat) # 切换帽子以防万一
		return
	target_x, target_y = next_apple_pos
	
	# 吃掉第一个苹果并开始长尾巴
	quick_print("开始游戏！第一个目标：", target_x, target_y)
	move(North) # 向任意方向移动一格来吃掉脚下的苹果
	tail.append((px, py)) # 将起始位置加入尾巴
	
	# 自我迭代循环
	while True:
		current_pos = (get_pos_x(), get_pos_y())
		target_pos = (target_x, target_y)
		
		# --- 3a. 移动到目标 ---
		while current_pos != target_pos:
			# 在移动前记录当前位置，用于更新尾巴
			last_pos = current_pos
			
			if not make_smart_move(target_x, target_y, tail, world_size):
				quick_print("被困住了！游戏结束。")
				change_hat(Hats.Gold_Hat) # 切换帽子以收获
				quick_print("收获骨头数量：", len(tail) * len(tail))
				return # 结束程序
			
			# 更新尾巴：将旧的头部位置加入，并移除末端，实现“移动”
			tail.insert(0, last_pos)
			tail.pop()
			
			current_pos = (get_pos_x(), get_pos_y())
			
		# --- 3b. 到达苹果位置 ---
		quick_print("到达苹果位置！尾巴长度：", len(tail))
		
		# [v1.4 修复] 使用同样健壮的检查来预知下一个苹果的位置
		next_apple_pos = measure()
		if not next_apple_pos:
			quick_print("已吃完全部苹果或发生错误！即将收获。")
			change_hat(Hats.Gold_Hat)
			quick_print("收获骨头数量：", len(tail) * len(tail))
			return
		next_target_x, next_target_y = next_apple_pos
		
		# 现在可以安全地吃掉当前苹果了
		# 寻找一个安全的方向来完成“吃”这个动作
		ate_apple = False
		eat_moves = [North, East, South, West]
		for direction in eat_moves:
			next_pos = get_next_pos(current_pos[0], current_pos[1], direction)
			if is_safe(next_pos, tail, world_size):
				move(direction)
				ate_apple = True
				break
		
		if not ate_apple:
			quick_print("被苹果困住了！游戏结束。")
			change_hat(Hats.Gold_Hat)
			quick_print("收获骨头数量：", len(tail) * len(tail))
			return
		
		# --- 3c. 更新状态 ---
		# 吃掉苹果，尾巴增长（只添加，不移除末端）
		tail.insert(0, target_pos) 
		target_x, target_y = next_target_x, next_target_y # 更新目标
		quick_print("新目标：", target_x, target_y)

while True:
	clear()
	main()

