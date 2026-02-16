from utils import *

threhold = 0

def for_all_custom(f):
	def row():
		f()
	for y in range(get_world_size()):
		if not spawn_drone(row):
			row()
		move(North)

def raw_task_power():
	while num_items(Items.Power) < threhold:
		if can_harvest():
			harvest()
		if get_ground_type() != Grounds.Soil:
			till()
		plant(Entities.Sunflower)
		if get_water() < 0.8:
			use_item(Items.Water)
		move(East)

def gain_power2(t):
	global threhold
	threhold = t
	move_to_beyond(0, 0)
	for_all_custom(raw_task_power)

def raw_task_harverst_all():
	for _ in range(get_world_size()):
		if can_harvest():
				harvest()
		move(East)

def harvest_all2():
	move_to_beyond(0, 0)
	for_all_custom(raw_task_harverst_all)
	move_to_beyond(0, 0)

def raw_task_harverst_all_soil():
	for _ in range(get_world_size()):
		if get_entity_type() != None:
			if can_harvest():
				harvest()
			else:
				till()
			if get_ground_type() == Grounds.Grassland:
				till()
		move(East)

def harvest_all_soil2():
	move_to_beyond(0, 0)
	for_all_custom(raw_task_harverst_all_soil)
	move_to_beyond(0, 0)

	