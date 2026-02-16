from utils import *

r_list = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9]

def force_plant_cactus():
	e_t = get_entity_type()
	if e_t != Entities.Cactus:
		if get_ground_type() == Grounds.Grassland:
			till()
		if e_t != None:
			if can_harvest():
				harvest()
			else:
				till()
				till()
		plant(Entities.Cactus)
	return measure()
	

def force_replant_cactus():
	if get_ground_type() == Grounds.Grassland:
		till()
	else:
		till()
		till()
	plant(Entities.Cactus)
	return measure()

def task_main():
	global task_y
	move_to_beyond(0, task_y)
	
	r_l = list((0,0,0,0,-1,-1,0,0,0,0))

	map = list()
	
	x = get_pos_x()
	while True:
		m = force_plant_cactus()
		first_check = True
		while not plant_right_cactus(x, m, r_l):
			if first_check and x == 15:
				if plant_right_next_cactus(x, m, r_l):
					swap(East)
					first_check = False
			m = force_replant_cactus()
		r_l[m] += 1
		map.append(m)
		x += 1
		if x == 32:
			break
		move(East)
	x = 31
	for i in range(31,1,-1):
		if map[i] != r_list[i]:
			while True:
				m1 = measure()
				move(West)
				x -= 1
				m2 = measure()
				if m2 != r_list[i] and m2 > m1:
					swap(East)
					map[x] = m1
					map[x+1] = m2
				if m2 == r_list[i]:
					break
			swap(East)
			map[x] = m1
			map[x+1] = m2
			while x < i-1:
				move(East)
				x += 1
				swap(East)
				map[x] = map[x+1]
				map[x+1] = m2
		else:
			move(West)
			x -= 1
	return
		
				

def plant_right_cactus(x, m, r_l):
	if r_l[m] > 2:
		return False
	if (x<16 and m>4) or (x>15 and m<5):
		return False
	return True
	
def plant_right_next_cactus(x, m, r_l):
	if m < 5 or m > 7:
		return False
	return True
	
def plant_right_help_cactus(x, m):
	if m != r_list[x]:
		return False
	return True

def task_main_drones():
	task_main()

world_size = get_world_size()
half_world = world_size//2
def gain_cactus(t=5000000):
	global threhold
	global task_y
	threhold = t

	while num_items(Items.Cactus) < threhold:
		drones = list()
		for task_y in range(1,world_size):
			drones.append(spawn_drone(task_main_drones))
		task_y = 0
		task_main()
		
		last = True
		for drone in drones:
			if drone == None:
				continue
			wait_for(drone)
			last = False
		if not last:
			sleep(1)
		harvest()
		move_to(0,0)

if __name__ == "__main__":
	harvest()
	move_to_beyond(0, 0)
	gain_cactus(10000000000)
	