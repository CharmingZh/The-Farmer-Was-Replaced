# =================================================================
#  贪吃蛇寻路AI v2.2 (语法约束版)
#  - 目标：通过AI算法，让贪吃蛇尽可能多地吃苹果，增长尾巴。
#
#  - [v2.2 核心改变]
#  - 1. (语法遵循): 移除了 `.get()` 方法，改用 `in` 关键字检查和直接访问字典。
#  - 2. (语法遵循): 将 `is None` 的判断改为 `== None`。
#  - 3. (语法遵循): 移除了主循环中的 `clear()` 调用。
#  - 4. (算法保持): 核心的汉密尔顿回路算法和逻辑保持不变。
# =================================================================

# ------------------ 核心AI辅助函数 ------------------

def create_hamiltonian_cycle_map(world_size):
	# 为给定大小的世界创建一个固定的“汉密尔顿回路”路径图。
	# 这个路径图确保蛇可以访问每一个格子而不会自我碰撞。
	# 该算法适用于拥有偶数宽度/高度的地图 (例如 32x32)。
	#
	# 路径模式：
	# - 第0行作为“返回走廊”。
	# - 其余行 (1 到 world_size-1) 采用蛇形填充模式。
	# - 最终形成一个覆盖所有格子的闭合回路。
	path_map = {}
	size = world_size

	# 步骤1: 填充 y >= 1 的蛇形路径
	for x in range(size):
		if x % 2 == 0:  # 偶数柱 (0, 2, ...), 路径向上
			if x > 0:
				# 从前一列的底部连接过来
				path_map[(x - 1, 1)] = East
			for y in range(1, size - 1):
				path_map[(x, y)] = North
			if x < size - 1:
				# 在顶部连接到下一列
				path_map[(x, size - 1)] = East
		else:  # 奇数柱 (1, 3, ...), 路径向下
			for y in range(size - 1, 1, -1):
				path_map[(x, y)] = South

	# 步骤2: 连接最后一列到返回走廊 (y=0)
	# 对于 size=32, 最后一列是 31 (奇数)。路径从 (30, size-1) 向东移动到 (31, size-1)
	# 然后在第31列向下移动到 (31, 1)，最后在 (31, 1) 向南移动到 (31, 0)
	path_map[(size - 1, 1)] = South

	# 步骤3: 建立 y=0 的返回走廊路径，一路向西
	for x in range(size - 1, 0, -1):
		path_map[(x, 0)] = West

	# 步骤4: 关闭回路，从 (0,0) 进入蛇形路径
	path_map[(0, 0)] = North

	return path_map

# ------------------ 主程序 ------------------

def main():
	# 将世界设置为一个更具挑战的大小 (必须是偶数)
	world_size = 32
	set_world_size(world_size)
	
	# 装备恐龙帽，开始游戏
	change_hat(Hats.Dinosaur_Hat)

	# --- AI初始化 ---
	# 预先计算覆盖全图的汉密尔顿回路
	quick_print("正在计算汉密尔顿回路...")
	path_map = create_hamiltonian_cycle_map(world_size)
	if not path_map or len(path_map) != world_size * world_size:
		quick_print("错误: 无法为当前地图尺寸生成有效的回路!")
		change_hat(Hats.Gold_Hat)
		return
	quick_print("回路计算完成！")
	
	# 初始化尾巴列表和当前位置
	# 注意：我们的 `tail` 列表是手动维护的，用于判断何时增长
	tail = [(get_pos_x(), get_pos_y())]
	
	# 获取第一个苹果的位置作为我们的目标
	next_apple_pos = measure()
	if not next_apple_pos:
		quick_print("错误: 无法在开始时测量到苹果位置!")
		change_hat(Hats.Gold_Hat)
		return
	target_x, target_y = next_apple_pos
	quick_print("开始游戏！第一个目标：", target_x, target_y)

	# --- 主循环 ---
	while True:
		# 获取当前蛇头位置
		px, py = get_pos_x(), get_pos_y()
		current_pos = (px, py)
		
		# 默认没有吃到苹果
		ate_apple = False

		# --- 1. 检查是否到达苹果位置 ---
		if current_pos == (target_x, target_y):
			ate_apple = True
			quick_print("到达苹果位置！当前尾巴长度:", len(tail))
			
			# 预先测量下一个苹果的位置
			next_apple_pos = measure()
			if not next_apple_pos:
				quick_print("已吃完全部苹果或发生错误！即将收获。")
				change_hat(Hats.Gold_Hat)
				quick_print("收获骨头数量：", len(tail) * len(tail))
				return
			
			# 更新目标为下一个苹果
			target_x, target_y = next_apple_pos
			quick_print("新目标：", target_x, target_y)

		# --- 2. 根据汉密尔顿地图决定下一步方向 ---
		direction = None # 先初始化方向
		if current_pos in path_map:
			direction = path_map[current_pos]
		
		# [v2.2 语法约束] 只有当路径图中找不到当前位置时 (即 direction 为 None) 才报错
		if direction == None:
			quick_print("错误: 当前位置不在预设计算路径上！游戏结束。")
			change_hat(Hats.Gold_Hat)
			quick_print("收获骨头数量：", len(tail) * len(tail))
			return

		# --- 3. 执行移动 ---
		if not move(direction):
			quick_print("移动失败，被困住了！游戏结束。")
			change_hat(Hats.Gold_Hat)
			quick_print("收获骨头数量：", len(tail) * len(tail))
			return # 结束程序

		# --- 4. 更新我们自己维护的尾巴列表 ---
		# 将旧的头部位置加入尾巴列表的前端
		tail.insert(0, current_pos)
		
		# 如果这个回合没有吃到苹果，就移除尾巴的末端来模拟“移动”
		# 如果吃到了苹果，则不移除，实现“增长”
		if not ate_apple:
			tail.pop()

# --- 循环运行主程序 ---
while True:
	main()

