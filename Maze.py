# =================================================================
#
#   --- 全地图灌木种植脚本 (v2, 优化版) ---
#
#   此脚本会自动扫描整个地图。
#   如果发现任何不是灌木的地块，它会将其清理并种上灌木。
#   为了确保种植不间断，它会在资源不足时自动寻找并收割草。
#   完成全图种植后，它会停在最后一个地块上，等待迷宮生成。
#
# =================================================================

# --- 辅助函数 ---

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
	# 扫描全图寻找可收割的草。
	# 注意：此函数会移动无人机，并将其留在找到草的位置（或扫描结束的位置）。
	# 它不负责将无人机移回原位。
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
				return (x, y) # 找到后立即返回坐标
			x = x + x_step
		y = y + 1
	return None # 扫描全图后未找到

# --- 主要逻辑 ---

def main():
	quick_print("启动全地图灌木种植程序...")
	n = get_world_size() 
	bush_cost = get_cost(Entities.Bush)
	
	if bush_cost == None:
		quick_print("错误：无法获取灌木的成本。脚本停止。")
		return

	# --- 蛇形扫描并种植 ---
	y = 0
	while y < n:
		x_start, x_end, x_step = (0, n, 1)
		if y % 2 != 0: # 奇数行反向
			x_start, x_end, x_step = (n - 1, -1, -1)
		
		x = x_start
		while x != x_end:
			move_to(x, y)
			if get_entity_type() != Entities.Bush:
				quick_print("地块 (", x, ",", y, ") 不是灌木，准备种植。")
				
				# 检查并补充资源
				while (Items.Hay in bush_cost and num_items(Items.Hay) < bush_cost[Items.Hay]) or (Items.Wood in bush_cost and num_items(Items.Wood) < bush_cost[Items.Wood]):
					quick_print("资源不足，需要干草或木材。开始寻找草...")
					
					grass_pos = find_harvestable_grass() # 此函数会移动无人机
					
					if grass_pos != None:
						# 无人机当前就在grass_pos，直接收获
						harvest()
						quick_print("收获了草。返回种植点。")
						move_to(x, y) # 操作完成后，必须明确返回到当前需要种植的地块
					else:
						quick_print("找不到可收割的草。返回原地等待草生长...")
						move_to(x, y) # 即使没找到，也要返回原位，避免位置错乱
						pass # 等待
				
				#clear()
				plant(Entities.Bush)
				quick_print("成功种植灌木。")

			x = x + x_step
		y = y + 1

	quick_print("全地图扫描和种植完成。")
	# --- 等待灌木成熟 ---
	quick_print("现在等待所有灌木成熟...")
	while True: # 无限循环直到所有灌木都成熟
		is_fully_mature = True
		y_check = 0
		# 开始全图扫描检查
		while y_check < n:
			x_check_start, x_check_end, x_check_step = (0, n, 1)
			if y_check % 2 != 0:
				x_check_start, x_check_end, x_check_step = (n - 1, -1, -1)
			
			x_check = x_check_start
			while x_check != x_check_end:
				move_to(x_check, y_check)
				if get_entity_type() == Entities.Bush and not can_harvest():
					is_fully_mature = False
					break # 发现未成熟的，中断内层循环
				x_check = x_check + x_check_step
			
			if not is_fully_mature:
				break # 中断外层循环
			y_check = y_check + 1
		
		if is_fully_mature:
			quick_print("所有灌木均已成熟！")
			break # 跳出等待循环
		else:
			quick_print("发现未成熟的灌木，继续等待...")

	# --- 检查资源并生成迷宫 ---
	quick_print("准备生成迷宫，正在检查资源...")
	min_substance = n * n # 需要n*n的资源来覆盖全图
	while num_items(Items.Weird_Substance) < min_substance:
		quick_print("Weird Substance 不足。需要: ", min_substance, ", 当前拥有: ", num_items(Items.Weird_Substance), ". 等待中...")

	quick_print("资源充足！开始生成巨型迷宫...")
	# 移动到一个角落 (0,0) 来施放全图效果
	move_to(0, 0)
	use_item(Items.Weird_Substance, n) # 使用道具并指定大小为 n

	if measure() != None:
		quick_print("巨型迷宫生成成功！脚本任务完成。")
	else:
		quick_print("错误：迷宫生成失败。请检查游戏状态。")
		
# --- 脚本入口 ---
main()
