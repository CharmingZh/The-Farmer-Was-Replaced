from builtins import abs, len, list, min, range, set, typ

def check_water(threshold=0.5):
	# """检查水分是否低于阈值，如果低于则使用水"""
	if get_water() < threshold:
		use_item(Items.Water)

def check_entities(entity_type):
	# """检查当前实体类型是否与预期不符，如果不符则进行相应操作"""
	entity_type_now = get_entity_type()
	ground_type_now = get_ground_type()
	if entity_type_now != entity_type:
		if entity_type == Entities.Grass:
			if ground_type_now == Grounds.Soil:
				till()
		elif entity_type == Entities.Bush:
			if ground_type_now == Grounds.Grassland:
				till()
		elif entity_type == Entities.Tree:
			if ground_type_now == Grounds.Grassland:
				till()
		elif entity_type == Entities.Carrot:
			if ground_type_now == Grounds.Grassland:
				till()
		elif entity_type == Entities.Sunflower:
			if ground_type_now == Grounds.Grassland:
				till()
		plant(entity_type)
		
def force_check_entities(entity_type):
	# """检查当前实体类型是否与预期不符，如果不符则进行相应操作"""
	entity_type_now = get_entity_type()
	if entity_type_now != entity_type:
		if get_entity_type() != None:
			while not can_harvest() and get_entity_type() != None:
				use_item(Items.Fertilizer)
			harvest()
		ground_type_now = get_ground_type()
		if entity_type == Entities.Grass:
			if ground_type_now == Grounds.Soil:
				till()
			return
		elif entity_type == Entities.Carrot:
			if ground_type_now == Grounds.Grassland:
				till()
		elif entity_type == Entities.Sunflower:
			if ground_type_now == Grounds.Grassland:
				till()
		plant(entity_type)

def check_v_in_list(v, v_list):
	# """检查值v是否在列表v_list中"""
	if v_list == None:
		return False
	if len(v_list) == 0:
		return False
	if v == None:
		return False
	for i in range(len(v_list)):
		if v == v_list[i]:
			return True
	return False

def copy_list(list1):
	# """复制列表"""
	if list1 == None:
		return None
	if len(list1) == 0:
		return []
	list2 = []
	for i in range(len(list1)):
		list2.append(list1[i])
	return list2

def create_2d_list(m, n, value):
	# """创建一个m行n列的二维列表，所有元素初始化为value"""
	if m <= 0 or n <= 0:
		return []
	for i in range(m):
		list_tem = []
		for j in range(n):
			list_tem.append(value)
		if i == 0:
			list_2d = [list_tem]
		else:
			list_2d.append(list_tem)
	return list_2d

def print_2d_list(list_2d):
	# """打印二维列表"""
	if list_2d == None:
		return
	if len(list_2d) == 0:
		return
	for i in range(len(list_2d)):
		for j in range(len(list_2d[i])):
			quick_print(i,j,list_2d[i][j])

def sleep(sec):
	# """暂停执行指定的秒数"""
	if sec <= 0:
		return
	time = get_time()
	while get_time() < time + sec:
		pass

field_size = get_world_size()  # 获取田地大小，是正方形
direction_horizontal = get_pos_x() != field_size - 1   # 水平移动方向
direction_vertical = get_pos_y() != field_size - 1	  # 垂直移动方向
direction_HV = True		  # 当前移动方向，水平还是垂直

def reset_move():
	# """重置移动方向"""
	global direction_horizontal
	global direction_vertical
	global direction_HV
	direction_horizontal = get_pos_x() != field_size - 1   # 水平移动方向
	direction_vertical = get_pos_y() != field_size - 1	  # 垂直移动方向
	direction_HV = True		  # 当前移动方向，水平还是垂直

def move_H(dir):
	# """水平移动 dir=True表示向右，False表示向左"""
	if dir:
		move(East)
	else:
		move(West)

def move_V(dir):
	# """垂直移动 dir=True表示向上，False表示向下"""
	if dir:
		move(North)
	else:
		move(South)

def move_robot():
	# """使用全局变量进行移动"""
	x, y = get_pos_x(), get_pos_y()
	global direction_horizontal
	global direction_vertical
	global direction_HV
	if direction_HV:  # 水平移动
		move_H(direction_horizontal)
		if get_pos_x() == field_size - 1 or get_pos_x() == 0:  # 到达边界
			direction_HV = False  # 改变移动方向为垂直
			direction_horizontal = not direction_horizontal  # 改变水平移动方向
	else:  # 垂直移动
		move_V(direction_vertical)
		direction_HV = True  # 改变移动方向为水平
		if get_pos_y() == field_size - 1 or get_pos_y() == 0:  # 到达边界
			direction_vertical = not direction_vertical  # 改变垂直移动方向

def move_to(x, y):
	# """移动到指定位置 (x, y)"""
	while get_pos_x() != x or get_pos_y() != y:
		if get_pos_x() < x:
			move(East)
		elif get_pos_x() > x:
			move(West)
		elif get_pos_y() < y:
			move(North)
		elif get_pos_y() > y:
			move(South)
	reset_move()

def move_to_beyond(x, y):
	# """移动到指定位置 (x, y)，考虑边界环绕"""
	while get_pos_x() != x or get_pos_y() != y:
		if get_pos_x() < x:
			if x - get_pos_x() > field_size - (x - get_pos_x()):
				move(West)
			else:
				move(East)
		elif get_pos_x() > x:
			if get_pos_x() - x > field_size - (get_pos_x() - x):
				move(East)
			else:
				move(West)
		elif get_pos_y() < y:
			if y - get_pos_y() > field_size - (y - get_pos_y()):
				move(South)
			else:
				move(North)
		elif get_pos_y() > y:
			if get_pos_y() - y > field_size - (get_pos_y() - y):
				move(North)
			else:
				move(South)
	reset_move()

def get_shortest_path(list_of_path):
	# """获取经过list_of_path中所有点的近似最短路径顺序"""
	if len(list_of_path) <= 1:
		return list_of_path

	world_size = get_world_size()

	path_order = []
	current_point = list_of_path[len(list_of_path)-1]
	while len(list_of_path) != 0:
		nearest_point = None
		min_distance = 999999999

		for point in list_of_path:
			dist = calculate_wrapped_distance(current_point, point, world_size)
			if dist < min_distance:
				min_distance = dist
				nearest_point = point

		path_order.append(nearest_point)
		list_of_path.remove(nearest_point)
		current_point = nearest_point

	return path_order

def calculate_wrapped_distance(point1, point2, world_size):
	# """计算在环绕世界中两个点之间的距离的平方"""
	x1, y1 = point1
	x2, y2 = point2

	# 计算x方向的最短距离（考虑环绕）
	dx = abs(x1 - x2)
	dx_wrapped = world_size - dx  # 环绕后的距离
	min_dx = min(dx, dx_wrapped)

	# 计算y方向的最短距离（考虑环绕）
	dy = abs(y1 - y2)
	dy_wrapped = world_size - dy  # 环绕后的距离
	min_dy = min(dy, dy_wrapped)

	# 返回欧几里得距离的平方
	return min_dx**2 + min_dy**2

def add_k_to_list_in_dict(k, v, dict):
	# """在字典的列表中添加键值对，如果键不存在则创建新列表"""
	if(k not in dict):
		l = list()
		l.append(v)
		dict[k] = l
	else:
		dict[k].append(v)
		
def add_k_to_set_in_dict(k, v, dict):
	# """在字典的列表中添加键值对，如果键不存在则创建新列表"""
	if(k not in dict):
		l = set()
		l.add(v)
		dict[k] = l
	else:
		dict[k].add(v)

def for_all(f):
	# """对整个田地执行函数 f"""
	def row():
		for _ in range(get_world_size()-1):
			f()
			move(East)
		f()
	for _ in range(get_world_size()):
		if not spawn_drone(row):
			row()
		move(North)

def replant(entity_type):
	if can_harvest():
		harvest()
	else:
		till()
		till()
	plant(entity_type)