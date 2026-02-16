import structs
import farm_util

def enqueue_harvest(heap, x, y, prio):
	structs.heap_push(heap, (prio, ('harvest', x, y)))

def enqueue_plant(heap, x, y, entity, prio):
	structs.heap_push(heap, (prio, ('plant', x, y, entity)))

def enqueue_water(heap, x, y, threshold, mod, prio):
	structs.heap_push(heap, (prio, ('water', x, y, threshold, mod)))
	
def enqueue_fertilize(heap, x, y, prio):
	structs.heap_push(heap, (prio, ('fertilize', x, y)))

def planner_run_all(heap):
	n = get_world_size()
	
	tasks_by_coord = {}
	while len(heap) > 0:
		prio, job = structs.heap_pop(heap)
		job_type = job[0]
		x, y = job[1], job[2]
		key = (x, y)
		
		if not (key in tasks_by_coord):
			tasks_by_coord[key] = {}
		
		if job_type == 'water':
			if 'water' in tasks_by_coord[key]:
				ex_th, ex_md = tasks_by_coord[key]['water']
				new_th, new_md = job[3], job[4]
				tasks_by_coord[key]['water'] = (max(ex_th, new_th), min(ex_md, new_md))
			else:
				tasks_by_coord[key]['water'] = (job[3], job[4])
		else:
			if len(job) > 3:
				tasks_by_coord[key][job_type] = job[3:]
			else:
				tasks_by_coord[key][job_type] = True

	y = 0
	while y < n:
		direction = 1
		x = 0
		if y % 2 != 0:
			direction = -1
			x = n - 1
		while x >= 0 and x < n:
			key = (x, y)
			if key in tasks_by_coord:
				run_cell_tasks(x, y, tasks_by_coord[key])
			x = x + direction
		y = y + 1
		
def run_cell_tasks(x, y, tasks):
	farm_util.move_to(x, y)
	et_before = get_entity_type()
	
	if 'harvest' in tasks:
		if can_harvest():
			harvest()
	
	if 'plant' in tasks:
		entity_to_plant = tasks['plant'][0]
		farm_util.ensure_ground_for(entity_to_plant)
		if get_entity_type() != entity_to_plant:
			plant(entity_to_plant)
	elif et_before != Entities.Sunflower and et_before != Entities.Cactus and et_before != None and get_entity_type() != et_before:
		farm_util.ensure_ground_for(et_before)
		plant(et_before)
	
	if 'water' in tasks:
		th, md = tasks['water']
		if get_water() < th:
			if (get_tick_count() + x + y) % md == 0:
				use_item(Items.Water)

	if 'fertilize' in tasks:
		if num_items(Items.Fertilizer) > 0 and not can_harvest():
			if farm_util.get_fert_count(x,y) < 1: # F_CAP_PER_CELL
				use_item(Items.Fertilizer)
				farm_util.inc_fert_count(x,y)