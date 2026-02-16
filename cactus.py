from utils import *

farm_list = dict()
plant_type = None
task_x = 0
task_y = 0
threhold = 0
r_d = dict({0:(0,1),1:(0,1),2:(0,1),3:(0,1),4:(0,1,2),5:(1,2),6:(1,2),
		7:(1,2,3),8:(2,3),9:(2,3),10:(2,3,4),11:(3,4),12:(3,4),13:(3,4),
		14:(4,5),15:(4,5),16:(4,5),17:(4,5),18:(5,6),19:(5,6),20:(5,6),
		21:(5,6,7),22:(6,7),23:(6,7),24:(6,7,8),25:(7,8),26:(7,8),
		27:(7,8,9),28:(7,8,9),29:(8,9),30:(8,9),31:(8,9)})

def task_main():
	global move_step
	global task_x
	global task_y
	move_to_beyond(0, task_y)

	if can_harvest():
		harvest()

	r_l = list((0,0,0,0,0,0,0,0,0,0))

	turn = 0
	while True:
		if get_ground_type() == Grounds.Grassland:
			till()
		x = get_pos_x()
		if x == 0:
			turn += 1
		if turn == 1:
			force_check_entities(Entities.Cactus)
			m = measure()
			first_check = True
			while not plant_right_cactus(x, m):
				if first_check and x < 29:
					if plant_right_next_cactus(x, m):
						swap(East)
						first_check = False
				if get_ground_type() == Grounds.Grassland:
					till()
				replant(Entities.Cactus)
				m = measure()
			if x < 31:
				r_l[m] += 1
				move(East)
			else:
				turn = 2
		elif turn == 2:
			if x < 31:
				break
			turn = 3
		elif turn < 32:
			move(North)
			m = measure()
			x = get_pos_x()
			y = get_pos_y()
			y_count = 5
			while plant_right_cactus(x, m):
				move(North)
				m = measure()
				if y_count == 0:
					return
				y_count -= 1
			check_timeout = 0
			for i in range(world_size//2):
				if get_ground_type() == Grounds.Grassland:
					break
				force_check_entities(Entities.Cactus)
				m = measure()
				retry = 0
				can_swap = True
				while (not plant_right_cactus(x, m)) and retry < 20:
					check_timeout = 0
					while check_timeout < 51:
						if get_ground_type() == Grounds.Grassland:
							break
						pass
						check_timeout += 1
					if check_timeout < 10:
						break
					if can_swap and x < 29:
						if plant_right_cactus(x - 1, m):
							swap(West)
							can_swap = False
					replant(Entities.Cactus)
					m = measure()
					retry += 1
				move(West)
				x = get_pos_x()
			if check_timeout < 10:
				break
			move_to_beyond(31, y)
			turn += 1
		else:
			break

def plant_right_cactus(x, m):
	r_list = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9]
	if m != r_list[x]:
		return False
	return True
	
def plant_right_next_cactus(x, m):
	r_list = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, None, None, None]
	if m != r_list[x]:
		return False
	return True

def task_main_drones():
	task_main()

world_size = get_world_size()
half_world = world_size//2
def gain_cactus(t=5000000):
	global threhold
	global task_x
	global task_y
	threhold = t

	while num_items(Items.Cactus) < threhold:
		drones = list()
		for task_y in range(0,world_size):
			drones.append(spawn_drone(task_main_drones))
		task_main()

		move_to_beyond(0,0)

		for drone in drones:
			if drone == None:
				continue
			wait_for(drone)
		sleep(1)
		harvest()

if __name__ == "__main__":
	harvest()
	gain_cactus(1000000000000)

	