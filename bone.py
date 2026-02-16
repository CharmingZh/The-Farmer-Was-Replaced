from utils import *


# 这是一个骨头农场脚本，用于种植和收获骨头作物。

set_world_size(16)
world_size = get_world_size()


change_hat(Hats.Traffic_Cone)
max_bone = world_size * world_size
move_to_beyond(world_size//2, world_size//2)

		
def clost_try(x, y):
	px = get_pos_x()
	py = get_pos_y()
	if px != x or get_pos_y() != y:
		if   px < x and x % 2 != 0:
			return move(East)
		elif px > x and x % 2 == 0:
			return move(West)
		elif py < y and y % 2 != 0:
			return move(North)
		elif py > y and y % 2 == 0:
			return move(South)
	return m_try()

def m_try(dx, dy, tail_end_x, tail_end_y):
	x = get_pos_x()
	y = get_pos_y()
	if x == 0:
		if y == 0:
			move(East)
			return East
		else:
			move(South)
			return South
	else:
		if y == (world_size-1):
			move(West)
			return West
		elif (bone_count<(world_size*2)) or (tail_end_y-y)>(bone_count//(world_size-1)) or tail_end_x==0 or y > tail_end_y:
			if dx == x or y > dy:
				if move(North):
					return North
		if y % 2 == 0:
			if x == (world_size-1):
				move(North)
				return North
			else:
				move(East)
				return East
		if y % 2 != 0:
			if x == 1:
				move(North)
				return North
			else:
				move(West)
				return West

bone_count = 0
tail_end_x = 0
tail_end_y = 0
def move_to_snake(x, y):
	global tail_end_x
	global tail_end_y
	global moves
	goled = True
	# """移动到指定位置 (x, y)"""
	while get_pos_x() != x or get_pos_y() != y:
		dir = m_try(x, y, tail_end_x, tail_end_y)
		moves.insert(0, dir)
		if goled:
			goled = False
			continue
		else:
			till_dir = moves.pop()
			if till_dir == North:
				tail_end_y += 1
			elif till_dir == South:
				tail_end_y -= 1
			elif till_dir == East:
				tail_end_x += 1
			elif till_dir == West:
				tail_end_x -= 1
	return True

moves = []
while True:
	change_hat(Hats.Dinosaur_Hat)
	not_golded = True
	moves = []
	next_x, next_y = measure()
	move_to(next_x, next_y)
	tail_end_x = next_x
	tail_end_y = next_y
	while not_golded:
		m = measure()
		if m == None:
			break
		next_x, next_y = m
		not_golded = move_to_snake(next_x, next_y)
		bone_count+=1
	change_hat(Hats.Traffic_Cone)