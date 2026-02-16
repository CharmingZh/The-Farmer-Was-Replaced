# =================================================================
#  南瓜·32×32·v10.2 (基于 v9.0 添加“全局终止”)
#  - 保留 v9.0 的全部核心逻辑 ("精准修复")
#
#  - [v10.2 修复 - 解决 "0次完成" 中的“不停止”问题]
#  - 1. (自动终止): 主机 (main) 检查南瓜数量，达标后发送信号。
#  - 2. (全局终止): 使用 Python 'global' 关键字 'STOP_WORKERS' 作为信号。
#  - 3. (工人响应): 子机 (row_worker) 检查该信号，收到后主动 return。
#  - 4. (速度修正): set_execution_speed(100) 已改为 0，用于最快挑战。
# =================================================================

# ------------------ 基础移动与路径 ------------------

def move_to(tx, ty):
	n = get_world_size()
	px = get_pos_x()
	py = get_pos_y()

	# ---- X 方向：选更短的环面距离 ----
	dx_fwd = (tx - px) % n
	dx_back = (px - tx) % n
	if dx_fwd <= dx_back:
		i = 0
		while i < dx_fwd:
			move(East)
			i = i + 1
	else:
		i = 0
		while i < dx_back:
			move(West)
			i = i + 1

	# 更新当前位置
	px = get_pos_x()
	py = get_pos_y()

	# ---- Y 方向：选更短的环面距离 ----
	dy_fwd = (ty - py) % n
	dy_back = (py - ty) % n
	if dy_fwd <= dy_back:
		j = 0
		while j < dy_fwd:
			move(North)
			j = j + 1
	else:
		j = 0
		while j < dy_back:
			move(South)
			j = j + 1

def build_snake_path(x0, y0, x1, y1):
	path = []
	y = y0
	while y <= y1:
		if ((y - y0) % 2) == 0:
			x = x0
			while x <= x1:
				path.append((x, y))
				x = x + 1
		else:
			x = x1
			while x >= x0:
				path.append((x, y))
				x = x - 1
		y = y + 1
	return path

# ------------------ 判定与操作 ------------------

def ensure_pumpkin_here():
	# 仅在非 Soil 时才 TILL
	if get_ground_type() != Grounds.Soil:
		till()
	if get_entity_type() != Entities.Pumpkin:
		plant(Entities.Pumpkin)

# 【v9.0 逻辑 - 保留】
def is_withered_here():
	# 检查当前地块是否为“枯死南瓜”
	if get_entity_type() == Entities.Pumpkin and not can_harvest():
		# 【性能瓶颈】在循环中调用 measure()
		mysterious_num = measure()
		if mysterious_num == 0:
			return True
	return False

# ------------------ 行维护工人 (v9.0 智能修复逻辑) ------------------

def row_worker(y_level):
	quick_print("ROW_WORKER_START", "Y_LEVEL", y_level, "", "", "", "")
	path = build_snake_path(0, y_level, 31, y_level)
	
	while True:
		# 【v10.2 添加】工人检查全局终止信号
		if STOP_WORKERS == 1:
			quick_print("ROW_WORKER_STOP", "Y_LEVEL", y_level, "SIGNAL_RECV", "", "", "")
			return # 收到信号，终止子无人机

		# --- 阶段 1: 扫描全行，并建立“枯死点”列表 ---
		withered_list = []
		i = 0
		while i < len(path):
			pos = path[i]
			move_to(pos[0], pos[1])
			
			entity = get_entity_type()
			if entity != Entities.Pumpkin:
				# 补种空地
				ensure_pumpkin_here()
			else:
				# 【v9.0 逻辑 - 保留】检查是否枯死
				if is_withered_here():
					# 是枯死南瓜，立即修复它，并加入列表以便后续反复检查
					plant(Entities.Pumpkin)
					withered_list.append(pos)
			i = i + 1
			
		# --- 阶段 2: 精准修复，直到“枯死点”列表清空 ---
		while len(withered_list) > 0:
			# 【v10.2 添加】在耗时较长的修复循环内也增加检查
			if STOP_WORKERS == 1:
				quick_print("ROW_WORKER_STOP (repair)", "Y_LEVEL", y_level, "SIGNAL_RECV", "", "", "")
				return
				
			still_withered = []
			j = 0
			while j < len(withered_list):
				pos = withered_list[j]
				move_to(pos[0], pos[1])
				
				# 【v9.0 逻辑 - 保留】再次检查该点是否已修复
				if is_withered_here():
					# 还没好，再次修复，并加入下一轮修复列表
					plant(Entities.Pumpkin)
					still_withered.append(pos)
				
				j = j + 1
			
			# 更新列表，继续循环直到全部修复
			withered_list = still_withered

# ------------------ 轻封装：生成子机 ------------------

def spawn_row_worker(y):
	def task():
		return row_worker(y)
	return spawn_drone(task)

# ------------------ 主程序 ------------------

def main():
	# 【v10.2 添加】声明并初始化全局变量
	global STOP_WORKERS
	STOP_WORKERS = 0
	
	# 【v10.2 修正】速度应设为 0 以进行最快挑战
	set_execution_speed(0)

	# 派发 31 个使用 v9.0 逻辑的子机
	want = 31
	free = max_drones() - num_drones()
	need = want
	if free < need:
		need = free
	used = 0
	y_spawn = 0
	while y_spawn < 31 and used < need:
		ok = spawn_row_worker(y_spawn)
		if ok:
			used = used + 1
		y_spawn = y_spawn + 1
	quick_print("DRONES_DISPATCHED", used, "OF", need, "FOR_ROWS", "0_TO", y_spawn - 1, "")
	quick_print("MAIN_ROLE", "HARVESTER_AND_WORKER_Y_31", "", "", "", "")

	# 主机（Harvester）负责 Y=31 行，并检查全局
	my_row = 31
	my_path = build_snake_path(0, my_row, 31, my_row)
	
	while True:
		# --- 主机阶段 1 & 2: 使用与子机相同的智能修复逻辑维护 Y=31 ---
		withered_list = []
		i = 0
		while i < len(my_path):
			pos = my_path[i]
			move_to(pos[0], pos[1])
			entity = get_entity_type()
			if entity != Entities.Pumpkin:
				ensure_pumpkin_here()
			else:
				# 【v9.0 逻辑 - 保留】
				if is_withered_here():
					plant(Entities.Pumpkin)
					withered_list.append(pos)
			i = i + 1
			
		while len(withered_list) > 0:
			# 【v10.2 添加】
			if STOP_WORKERS == 1:
				return

			still_withered = []
			j = 0
			while j < len(withered_list):
				pos = withered_list[j]
				move_to(pos[0], pos[1])
				# 【v9.0 逻辑 - 保留】
				if is_withered_here():
					plant(Entities.Pumpkin)
					still_withered.append(pos)
				j = j + 1
			withered_list = still_withered
		
		# --- 主机阶段 3: 检查全局并就地收获 ---
		move_to(0, 0)
		id1 = measure()
		move_to(31, 31)
		id2 = measure()
		
		# 【v10.2 添加】胜利检查 (目标: 200,000,000)
		pumpkin_count = num_items(Items.Pumpkin)
		if pumpkin_count >= 200000000:
			quick_print("GOAL_REACHED (pre-check)", "PUMPKINS", pumpkin_count, "TERMINATING_ALL", "", "", "")
			STOP_WORKERS = 1 # 设置全局变量
			return # 终止主机
		
		if id1 == None or id2 == None:
			continue
		
		if id1 > 0 and id1 == id2:
			quick_print("GIANT_ID_MATCH", "ID", id1, "HARVESTING_AT_CORNER", "", "", "")
			# 在当前位置 (31, 31) 就地收获
			if can_harvest():
				harvest()
				# 就地补种，开始下一轮
				ensure_pumpkin_here()
			else:
				quick_print("GIANT_ID_MATCH_ERR", "ID", id1, "CORNER_NOT_READY", "", "", "")
		
		# 【v10.2 添加】在循环末尾再次检查胜利条件
		pumpkin_count = num_items(Items.Pumpkin)
		if pumpkin_count >= 200000000:
			quick_print("GOAL_REACHED (post-check)", "PUMPKINS", pumpkin_count, "TERMINATING_ALL", "", "", "")
			STOP_WORKERS = 1 # 设置全局变量
			return # 退出 main 函数，终止主机

main()