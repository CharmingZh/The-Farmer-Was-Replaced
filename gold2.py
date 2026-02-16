from utils import *

directions = list()
directions_indexs = dict()
try_dirs = []
move_to_start_dir = None

def reset_dirction(x, y, gold_x, gold_y):
	global directions
	global directions_indexs
	if abs(gold_x-x)>abs(gold_y-y):
		if gold_x>x:
			if gold_y>y:
				directions = (East, North, South, West)
				directions_indexs = {East:0, North:1, South:2, West:3}
			else:
				directions = (East, South, North, West)
				directions_indexs = {East:0, South:1, North:2, West:3}
		else:
			if gold_y>y:
				directions = (West, North, South, East)
				directions_indexs = {West:0, North:1, South:2, East:3}
			else:
				directions = (West, South, North, East)
				directions_indexs = {West:0, South:1, North:2, East:3}
	else:
		if gold_x>x:
			if gold_y>y:
				directions = (North, East, West, South)
				directions_indexs = {North:0, East:1, West:2, South:3}
			else:
				directions = (South, East, West, North)
				directions_indexs = {South:0, East:1, West:2, North:3}
		else:
			if gold_y>y:
				directions = (North, West, East, South)
				directions_indexs = {North:0, West:1, East:2, South:3}
			else:
				directions = (South, West, East, North)
				directions_indexs = {South:0, West:1, East:2, North:3}
				
def reset_dirction2(x, y, gold_x, gold_y):
	global directions
	global directions_indexs
	if abs(gold_y-y)>abs(gold_x-x):
		if gold_x>=x:
			if gold_y>=y:
				directions = (East, North, South, West)
				directions_indexs = {East:0, North:1, South:2, West:3}
			else:
				directions = (East, South, North, West)
				directions_indexs = {East:0, South:1, North:2, West:3}
		else:
			if gold_y>=y:
				directions = (West, North, South, East)
				directions_indexs = {West:0, North:1, South:2, East:3}
			else:
				directions = (West, South, North, East)
				directions_indexs = {West:0, South:1, North:2, East:3}
	else:
		if gold_x>=x:
			if gold_y>=y:
				directions = (North, East, West, South)
				directions_indexs = {North:0, East:1, West:2, South:3}
			else:
				directions = (South, East, West, North)
				directions_indexs = {South:0, East:1, West:2, North:3}
		else:
			if gold_y>=y:
				directions = (North, West, East, South)
				directions_indexs = {North:0, West:1, East:2, South:3}
			else:
				directions = (South, West, East, North)
				directions_indexs = {South:0, West:1, East:2, North:3}
				
				
def try_move(x, y, direction):
	global reject_list
	if (x,y) in reject_list and direction in reject_list[(x,y)]:
		return None
	add_k_to_list_in_dict((x,y), direction, reject_list)
	if(not move(direction)):
		return None
	(x,y) = (get_pos_x(),get_pos_y())
	add_k_to_list_in_dict((x,y), get_back(direction), reject_list)
	return direction

def get_back_index(direction):
	for key in directions_indexs:
		if key == get_back(direction):
			return directions_indexs[key]

def get_back(direction):
	if direction == North:
		return South
	if direction == South:
		return North
	if direction == West:
		return East
	if direction == East:
		return West

def get_dirs_not_in_list(direction_list):
	result = list()
	for dir in directions:
		if dir not in direction_list:
			result.insert(0, dir)
	return result

parent_last_move = None
def task_branch():
	global reject_list
	global parent_last_move
	global harvest_count
	global gold_x_o
	global gold_y_o

	# 尝试移动到起始方向
	if move(get_back(parent_last_move)) == False:
		return

	# 初始化变量
	(gold_x, gold_y) = (gold_x_o, gold_y_o)
	(x,y) = (get_pos_x(),get_pos_y())
	only_pop = False
	if_pop_then_die = 0
	moves = []

	while True:
		# 如果金块位置变化，说明被其他无人机采集，任务结束
		if (gold_x, gold_y) != (gold_x_o, gold_y_o):
			return
		# 重置优先方向
		rf(x, y, gold_x, gold_y)
		last_direction = None

		(px, py) = (x, y)
		# 如果不是仅弹出上一步，则尝试所有方向移动
		if not only_pop:
			test_dir = 0
			drone = None
			for dir in directions:
				test_dir += 1
				# 尝试移动。try_move会检查拒绝列表，若在拒绝列表中则不移动、若不在则首先将该方向加入拒绝列表。然后尝试移动，
				# 如果移动成功，返回移动方向，并将来时的方向加入新位置的拒绝列表；否则返回None
				last_direction = try_move(x, y, dir) # 如果移动成功，返回方向，否则返回None。会移动到新位置
				if last_direction != None:
					# 如果到达金块位置，则处理采集
					if (get_pos_x(),get_pos_y()) == measure():
						harvest_count += 1
						# 如果采集次数未达上限，则使用奇异物质增加采集量
						if harvest_count < 300:
							use_item(Items.Weird_Substance, weird_count)
						else:
							harvest()
						return

					# 如果移动方向不是最后一个尝试的方向，则生成新的无人机回到上一步位置，继续尝试其他方向
					if test_dir != 4:
						parent_last_move = last_direction
						drone = spawn_drone(task_branch)
						# 如果生成无人机成功，则将上一步位置的其他方向加入拒绝列表
						if drone != None:
							for dir_p in directions:
								add_k_to_list_in_dict((px, py), dir_p, reject_list)
					break
			# 如果所有方向均尝试失败，则准备回退
			only_pop = (test_dir == 4)

		# 如果移动成功，则last_direction不为None，记录移动方向，否则准备回退
		if (last_direction != None):
			# 如果moves列表为空，且之前点在拒绝列表中且拒绝列表长度为4，说明此点所有方向均尝试过，不再记录此点
			if (len(moves) == 0) and (reject_list[(px, py)] != None) and (len(reject_list[(px, py)]) == 4):
				moves.append(list((last_direction, only_pop)))
				only_pop = False
			else:
				moves.append(list((last_direction, only_pop)))
				only_pop = False
				if_pop_then_die += 1
		else:
			if len(moves) == 0 or if_pop_then_die == 0:
				return
			(last_direction_back, only_pop) = moves.pop()
			move(get_back(last_direction_back))
			if_pop_then_die -= 1
		gold_point = measure()
		if gold_point == None:
			return
		(gold_x, gold_y) = gold_point
		(x,y) = (get_pos_x(),get_pos_y())

reject_list = dict()
harvest_count = 0
weird_count = 0
gold_x_o = 0
gold_y_o = 0
x=0
y=0
maze_size = 32
threhold = 0
def task_main_drones():
	global x
	global y
	global gold_x_o
	global gold_y_o
	global harvest_count
	move_to_beyond(x,y)
	harvest_count = 0
	time = get_time()
	while num_items(Items.Gold) < threhold:
		m = measure()
		if m == None:
			harvest_count = 0
		elif (x, y) == m:
			if harvest_count==301:
				harvest()
			else:
				use_item(Items.Weird_Substance, weird_count)
				harvest_count+=1
				time = get_time()
		elif (gold_x_o, gold_y_o) != m:
			(gold_x_o, gold_y_o) = m
			release_task_drone()
			harvest_count += 1
			time = get_time()
		elif time + 10 < get_time():
			release_task_drone()
			harvest_count += 1
			time = get_time()
	return

drone_id = 0
def release_task_drone():
	global parent_last_move
	global rf
	global drone_id
	dirs = list((East,North,West,South))
	while len(dirs)>0:
		parent_last_move = dirs[len(dirs)-1]
		drone_id += 1
		if drone_id%2 == 0:
			rf = reset_dirction
		else:
			rf = reset_dirction2
		drone = spawn_drone(task_branch)
		if drone != None:
			dirs.pop()

rf = reset_dirction
def gain_gold(t=500000):
	global weird_count
	global x
	global y
	global reject_list
	global harvest_count
	global weird_count
	global gold_x_o
	global gold_y_o
	global threhold
	global rf
	threhold = t
	corner_close = maze_size**(1/2)//1
	corner_far = maze_size-1-corner_close
	half_size = maze_size//2
	weird_count = 32 * maze_size
	drone = 0
	for (x,y) in ((corner_close,corner_far), (corner_far,corner_close), (corner_far,corner_far),
			   (half_size,half_size), (corner_close,half_size), (half_size,corner_close),
			   (corner_far,half_size), (half_size,corner_far)):
		if drone%2 == 0:
			rf = reset_dirction
		else:
			rf = reset_dirction2
		spawn_drone(task_main_drones)
	move_to_beyond(corner_close,corner_close)
	if(can_harvest()):
		harvest()
	if(get_ground_type()==Grounds.Soil):
		till()
	sleep(1)


	x = corner_close
	y = corner_close
	harvest_count = 0
	time = get_time()
	while num_items(Items.Gold) < threhold:
		m = measure()
		if m == None:
			sleep(0.2)
			plant(Entities.Bush)
			use_item(Items.Weird_Substance, weird_count)
			harvest_count = 0
			(gold_x_o, gold_y_o) = measure()
			release_task_drone()
		elif (x, y) == m:
			if harvest_count==301:
				harvest()
			else:
				use_item(Items.Weird_Substance, weird_count)
				harvest_count+=1
				time = get_time()
		elif (gold_x_o, gold_y_o) != m:
			(gold_x_o, gold_y_o) = m
			release_task_drone()
			harvest_count += 1
			time = get_time()
		elif time + 10 < get_time():
			release_task_drone()
			harvest_count += 1
			time = get_time()


if __name__ == "__main__":
	harvest()
	gain_gold(1000000000)
	