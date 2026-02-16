from utils import *

farm_list = dict()
plant_type = None
task_x = 0
task_y = 0
threhold = 0
def task_main():
	global move_step
	global task_x
	global task_y
	global plant_type
	global time
	move_to_beyond(task_x, task_y)

	if can_harvest():
		harvest()
	if get_ground_type() == Grounds.Grassland:
		till()

	while get_time() < time + 1:
		pass


	if move_step == 0:
		move_steps = [North,North,North,North,North,East,East,East,East,East,South,South,South,South,South,West,West,West,
				North,North,North,East,South,South,East,North,North,North,West,West,West,South,South,South,South,West]
		measure_list = [0, 5, 10]
		measure_b_list = [1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14]
		harvest_time = [5, 10, 15]

	else:
		move_steps = [East,East,North,North,North,North,North,West,West,West,West,West,South,South,South,South,South,East,
				North,North,North,North,East,East,East,South,South,South,West,North,North,West,South,South,South,East]
		measure_list = [2, 7, 12]
		measure_b_list = [3, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16]
		harvest_time = [7, 12, 17]

	measure_value = None
	while num_items(Items.Pumpkin) < threhold:
		if move_step in harvest_time and can_harvest():
			if measure_value != None:
				m = measure()
				if m != None and m == measure_value:
					harvest()
					measure_value = None
		elif move_step in measure_b_list and measure_value != None:
			m = measure()
			if m == None or m != measure_value:
				measure_value = None
		if move_step in measure_list:
			measure_value = measure()
		if get_entity_type() != Entities.Pumpkin:
			plant(Entities.Pumpkin)
		if get_water() < 0.9:
			use_item(Items.Water)
		move(move_steps[move_step])
		move_step = (move_step + 1) % len(move_steps)

def task_branch():
	global plant_type
	move_to_beyond(task_x, task_y)
	force_check_entities(plant_type)

def task_main_drones():
	task_main()

water_points = []
def task_water_drones():
	global task_x
	global task_y
	global water_points
	while num_items(Items.Weird_Substance) < threhold:
		for (task_x, task_y) in water_points:
			move_to_beyond(task_x, task_y)
			while get_water() < 0.8:
				use_item(Items.Water)

time = None
def gain_pumpkin(t=5000000):
	global threhold
	global task_x
	global task_y
	global water_points
	global move_step
	global time
	threhold = t
	world_size = get_world_size()
	time = get_time()

	move_step = 0
	for task_x in range(0,world_size-6,8):
		for task_y in range(0,world_size-6,8):
			spawn_drone(task_main_drones)
	move_step = 18
	for task_x in range(1,world_size-5,8):
		for task_y in range(0,world_size-6,8):
			spawn_drone(task_main_drones)
	# task_x = 1
	# task_y = 0
	task_main()

if __name__ == "__main__":
	harvest()
	gain_pumpkin(300000000)

	