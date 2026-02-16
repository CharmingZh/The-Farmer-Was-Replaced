from utils import *
from collections import *

world_size = get_world_size()
farm_map = create_2d_list(world_size, world_size, None)
companion_map = create_2d_list(world_size, world_size, None)
requests = {}
success_count = 0

def my_plant(entity_type):
	global farm_map
	if can_harvest():
		harvest()
	elif get_entity_type() != Entities.Dead_Pumpkin:
		till()
		till()
	check_entities(entity_type)
	farm_map[get_pos_x()][get_pos_y()] = entity_type

def check_tree_slot(x, y):
	global farm_map
	for i in range(-1, 2):
		for j in range(-1, 2):
			if i == 0 and j == 0:
				continue
			new_x = x + i
			new_y = y + j
			if 0 <= new_x < world_size and 0 <= new_y < world_size:
				if farm_map[new_x][new_y] == Entities.Tree:
					return False
	return True

def check_companion_available(x, y, plant_type):
	if companion_map[x][y] == None:
		return 1
	if companion_map[x][y][0] == plant_type:
		return 2
	return 0

def has_sparse_area(x, y):
	# 检查(x,y)周围3步内空格子比例是否超过33%
	# 使用曼哈顿距离，考虑环形世界边界
	global farm_map
	world_size = get_world_size()
	world_max = world_size - 1
	empty_count = 0
	total_count = 2

	# 检查周围3步内的所有格子
	for dx in range(-3, 4):
		for dy in range(-3, 4):
			# 曼哈顿距离检查
			if abs(dx) + abs(dy) > 3:
				continue
			elif dx == 0 and dy == 0:
				continue

			# 计算实际坐标（考虑环形世界）
			actual_x = (x + dx) % world_size
			actual_y = (y + dy) % world_size

			# 检查格子是否为空
			if farm_map[actual_x][actual_y] == None:
				empty_count += 1
			if empty_count > 7:
				return True
	return False

def main_first_turn():
	global companion_map
	global success_count
	global requests
	x = 0
	y = 0
	plant_num = min(num_items(Items.Hay), num_items(Items.Carrot), num_items(Items.Wood))
	if num_items(Items.Hay) == plant_num:
		default_plant_type = Entities.Grass
	elif num_items(Items.Wood) == plant_num:
		default_plant_type = Entities.Tree
	else:
		default_plant_type = Entities.Carrot
	empty_farm_map = dict()
	for i in range(world_size):
		empty_farm_map[i]=list()
		for j in range(world_size):
			empty_farm_map[i].append(j)
	plant_type = default_plant_type
	while True:
		move_to_beyond(x, y)

		for key in empty_farm_map:
			y = empty_farm_map[key][0]
			x = key
			empty_farm_map[key].pop(0)
			if len(empty_farm_map[key]) == 0:
				empty_farm_map.pop(key)
			break

		not_fail = True
		should_retry = True
		while should_retry:
			my_plant(plant_type)
			plant_type_temp, (x, y) = get_companion()
			companion_available = check_companion_available(x, y, plant_type_temp)
			if companion_available > 0:
				plant_type = plant_type_temp
				break
			not_fail = has_sparse_area(x, y)

		if plant_type == Entities.Tree:
			use_item(Items.Water)

		if (x, y) not in requests:
			requests[(x, y)] = {Entities.Grass: [], Entities.Bush: [], Entities.Tree: [], Entities.Carrot: []}
		requests[(x, y)][plant_type].append((get_pos_x(), get_pos_y()))

		companion_map[get_pos_x()][get_pos_y()] = list((plant_type, (x, y), companion_available))
		if not companion_available == 1:
			if len(empty_farm_map) == 0:
				break
			plant_type = default_plant_type
		elif companion_available != 0:
			success_count += 1

	companion_rate = success_count/(world_size*world_size)
	return companion_rate

def main_optimization(companion_rate, threhold=0.85):
	global companion_map
	global success_count
	global requests
	global farm_map

	old_ccompanion_rate = 0
	while companion_rate < threhold and old_ccompanion_rate < companion_rate:
		# 遍历每个格子，如果requests中有该格子，且作物类型与当前格子不同，则收获后种植requests中出现次数最多的作物，然后覆写companion_map（如果次数相同，则保持不变）
		# 覆写时，首先更新获取该格子的companion信息，然后利用requests中该格子的需求信息，修改需求格子处的companion信息，将满足的需求格子处的companion_available设为3，而原先满足现在不满足的需求格子处的companion_available设为0
		# 最后，更新success_count，值为+满足需求格子数-不满足需求格子数
		need_test_raw_temp = set()
		need_test_line_temp = set()
		for j in range(world_size):
			for i in range(world_size):
				if (i, j) in requests:
					# 统计requests中每种作物的数量
					counts = {Entities.Grass: len(requests[(i, j)][Entities.Grass]), 
							Entities.Bush: len(requests[(i, j)][Entities.Bush]), 
							Entities.Tree: len(requests[(i, j)][Entities.Tree]), 
							Entities.Carrot: len(requests[(i, j)][Entities.Carrot])}
					# 找出数量最多的作物
					max_count = 0
					max_types = []
					for k in counts:
						if counts[k] < max_count:
							continue
						elif counts[k] > max_count:
							max_count = counts[k]
							max_types = []
						max_types.append(k)
					if max_count == 0:
						continue
					# 如果当前格子的作物存在于max_types中，则不进行任何操作
					old_e_type = farm_map[i][j]
					if old_e_type in max_types:
						continue
					# 否则，收获当前格子的作物，种植max_types
					max_type = max_types[0]
					move_to_beyond(i, j)
					old_r_type, (x, y) = get_companion()
					requests[(x, y)][old_r_type].remove((i, j))
					my_plant(max_type)
					# 覆写companion_map
					plant_type, (x, y) = get_companion()
					companion_available = check_companion_available(x, y, plant_type)
					companion_map[i][j] = list((plant_type, (x, y), companion_available))
					# 更companion_map
					if (x, y) not in requests:
						requests[(x, y)] = {Entities.Grass: [], Entities.Bush: [], Entities.Tree: [], Entities.Carrot: []}
					requests[(x, y)][plant_type].append((get_pos_x(), get_pos_y()))
					# 更新requests中该格子的需求格子处的companion信息
					for e_type in requests[(i, j)]:
						if e_type == max_type:
							for (req_x, req_y) in requests[(i, j)][e_type]:
								companion_map[req_x][req_y][2] = 3
								success_count += 1
						elif e_type == old_e_type:
							for (req_x, req_y) in requests[(i, j)][e_type]:
								companion_map[req_x][req_y][2] = 0
								success_count -= 1
					if companion_available > 0:
						success_count += 1

		old_ccompanion_rate = companion_rate
		companion_rate = success_count/(world_size*world_size)

	print(companion_rate*100, "%")
	farm_map = create_2d_list(world_size, world_size, None)
	companion_map = create_2d_list(world_size, world_size, None)
	empty_farm_map = []
	requests = {}
	success_count = 0

def gain_companion(hay=-1, wood=-1, carrot=-1):
	while ((hay==-1 and wood==-1 and carrot==-1) or
		(num_items(Items.Carrot)<carrot) or
		(num_items(Items.Wood)<wood) or
		(num_items(Items.Hay)<hay)):
		from collections import check_power
		check_power()
		move_to_beyond(0,0)
		main_optimization(main_first_turn(), 0.8)

if __name__ == "__main__":
	gain_companion()