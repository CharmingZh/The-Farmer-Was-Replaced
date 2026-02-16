from utils import *

farm_list = dict()
plant_type = None
task_x = 0
task_y = 0
threhold = 0
def task_main():
	global task_x
	global task_y
	global plant_type
	move_to_beyond(task_x, task_y)
	
	if can_harvest():
		harvest()
	if get_ground_type() == Grounds.Soil:
		till()
		
	while num_items(Items.Weird_Substance) < threhold:
		plant_type, (task_x, task_y) = get_companion()
		if (task_x, task_y) not in farm_list or farm_list[(task_x, task_y)] != plant_type:
			drone = None
			while drone == None:
				drone = spawn_drone(task_branch)
			wait_for(drone)
		while not can_harvest():
			pass
		use_item(Items.Fertilizer)
		harvest()
	
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

def gain_weird(t=5000000):
	global threhold
	global task_x
	global task_y
	global water_points
	threhold = t
	world_size = get_world_size()
	
	for task_x in range(3,world_size,8):
		for task_y in range(3,world_size,8):
			spawn_drone(task_main_drones)
			water_points.append((task_x, task_y))
			
	spawn_drone(task_water_drones)
		
if __name__ == "__main__":
	harvest()
	gain_weird(16000000)
	