from utils import *
from collections2 import *

#gain_power2(20000)
#harvest_all2()

drone_count = 1
move_to_beyond(0,0)

def companion_point_is_about_to_move(x, y, h_dir):
	current_x = get_pos_x()
	current_y = get_pos_y()

	# 条件1：点在当前位置上方（包括环绕）
	# 计算垂直方向的最短距离（考虑环绕）
	vertical_diff = (y - current_y) % 32
	if vertical_diff != 0 and vertical_diff <= 16:
		return True

	# 条件2：点在位移方向上且不超过3格（不穿过水平环绕）
	if h_dir == 1:  # 向右移动
		if y == current_y:  # 同一行
			horizontal_diff = (x - current_x) % 32
			if horizontal_diff <= 3:  # 不超过3格且不是自身
				if (current_x < 16 and x > 15) or (current_x > 15 and x < 16):
					return False
				return True
	elif h_dir == -1:  # 向左移动
		if y == current_y:  # 同一行
			horizontal_diff = (current_x - x) % 32
			if horizontal_diff <= 3:  # 不超过3格且不是自身
				if (current_x < 16 and x > 15) or (current_x > 15 and x < 16):
					return False
				return True
	return False

def get_min_plant():
	plant_num = min(num_items(Items.Hay), num_items(Items.Carrot), num_items(Items.Wood))
	if num_items(Items.Hay) == plant_num:
		return Entities.Grass
	elif num_items(Items.Wood) == plant_num:
		return Entities.Tree
	else:
		return Entities.Carrot

def replant(entity_type):
	if can_harvest():
		harvest()
	else:
		till()
		till()
	plant(entity_type)

def raw_task_power():
	# 移动到工作区域
	if drone_count % 2 != 0:
		move_to_beyond(0, (drone_count-1)*2%get_world_size())
	else:
		move_to_beyond(31, drone_count*2%get_world_size())

	x = get_pos_x()
	y = get_pos_y()
	if x == 0:
		h_dir = 1
	else:
		h_dir = -1
	move_up = False

	com_list = dict()
	
	line_time = 0
	check_time = 1
	last_3_dict = {}
	last_3x_list = []

	x = get_pos_x()
	y = get_pos_y()
	while True:
		if (x,y) in com_list and com_list[(x,y)] != None:
			plant_type = com_list[(x,y)]
			com_list[(x,y)] = None
		else:
			plant_type = get_min_plant()

		if(can_harvest()):
			harvest()
		force_check_entities(plant_type)

		retry = True
		while True:
			if get_entity_type() == None:
				force_check_entities(plant_type)
			plant_type_c, (x, y) = get_companion()
			if x in last_3_dict and last_3_dict[x] == plant_type_c:
				break
			if not companion_point_is_about_to_move(x, y, h_dir):
				replant(plant_type)
				continue
			if (x,y) in com_list and com_list[(x,y)] != None and com_list[(x,y)] != plant_type_c:
				replant(plant_type)
				continue
			break
		com_list[(x,y)] = plant_type_c

		if move_up:
			if (get_time() - first_time) > check_time * delay:
				check_time += 1
			while line_time >= (check_time * 3 - 1):
				if (get_time() - first_time) > check_time * delay:
					check_time += 1
			line_time += 1
			move(North)
			last_3x_list = []
			last_3_dict = {}
			move_up = False
			y = get_pos_y()
			continue
		elif h_dir == 1:
			move(East)
		else:
			move(West)
			
		if len(last_3x_list) == 3:
			last_3x_list.pop()
		last_3x_list.insert(0, x)
		last_3_dict[x] = plant_type

		x = get_pos_x()

		if x == 0 or x == 16:
			h_dir = 1
			move_up = True
		elif x == 15 or x == 31:
			h_dir = -1
			move_up = True

def raw_task_water():
	# 移动到工作区域
	if drone_count % 2 != 0:
		move_to_beyond(0, (drone_count-1)*2%get_world_size())
	else:
		move_to_beyond(31, drone_count*2%get_world_size())

	x = get_pos_x()
	if x == 0:
		h_dir = 1
	else:
		h_dir = -1
	move_up = False

	line_time = 0
	check_time = 1
	
	while True:

		while get_water() < 0.99:
			use_item(Items.Water)

		if move_up:
			if (get_time() - first_time) > check_time * 3.35:
				check_time += 1
			while line_time >= (check_time * 3 - 1):
				if (get_time() - first_time) > check_time * 3.35:
					check_time += 1
			line_time += 1
			move(North)
			move_up = False
			continue
		elif h_dir == 1:
			move(East)
		else:
			move(West)

		x = get_pos_x()

		if x == 0 or x == 16:
			h_dir = 1
			move_up = True
		elif x == 15 or x == 31:
			h_dir = -1
			move_up = True
			
first_time = 0
delay = 14.3
def for_companion():
	global drone_count
	global first_time
	first_time = get_time()
	while drone_count <= 16:
		if not spawn_drone(raw_task_water):
			raw_task_water()
		drone_count += 1
	while drone_count <= 32:
		if not spawn_drone(raw_task_power):
			raw_task_power()
		drone_count += 1

for_companion()
#for_test()