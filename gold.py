from utils import *

directions = list()
directions_indexs = dict()

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

def try_move(x, y, direction, reject_list):
	if (x,y) in reject_list and direction in reject_list[(x,y)]:
		return None, reject_list
	add_k_to_list_in_dict((x,y), direction, reject_list)
	if(not move(direction)):
		return None, reject_list
	(x,y) = (get_pos_x(),get_pos_y())
	add_k_to_list_in_dict((x,y), get_back(direction), reject_list)
	return direction, reject_list
	
def get_back_index(direction):
	for key in directions_indexs:
		if key == direction:
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

def gain_gold(threhold=500):
	global directions
	global directions_indexs
	if(can_harvest()):
		harvest()
	if(get_ground_type()==Grounds.Soil):
		till()
	# check_power()
	
	harvest_count = 0
	maze_size = 2
	weird_count = 32 * maze_size
	while num_items(Items.Gold) < threhold:
		harvest_count = 0
		move_to_beyond(maze_size//2,maze_size//2)
		plant(Entities.Bush)
		while harvest_count < 300:
			use_item(Items.Weird_Substance, weird_count)
			
			reject_list = dict()
			moves = list()
			(x,y) = (get_pos_x(),get_pos_y())
			(gold_x, gold_y) = measure()
			last_direction_back = None
			only_pop = False
			while not (gold_x, gold_y) == (x,y):
				reset_dirction(x, y, gold_x, gold_y)
				if not only_pop:
					test_dir = 0
					for dir in directions:
						test_dir += 1
						last_direction, reject_list = try_move(x, y, dir, reject_list)
						if last_direction != None:
							last_direction_back = get_back(last_direction)
							break
					only_pop = (test_dir == 4)
				if (last_direction != None):
					moves.append(list((last_direction, only_pop)))
					only_pop = False
				else:
					(last_direction_back, only_pop) = moves.pop()
					move(get_back(last_direction_back))
				(x,y) = (get_pos_x(),get_pos_y())
				(gold_x, gold_y) = measure()
			harvest_count += 1
		harvest()

harvest()	
gain_gold(5120000000)