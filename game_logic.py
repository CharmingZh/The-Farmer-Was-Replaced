import config
import farm_util
import index_mod
import sun_mod
import cactus_mod
import planner

def init_game():
	index_mod.init_maps()
	n = get_world_size()
	cx0 = max(2, (n // 2) - 2)
	cx1 = cx0 + 3
	cy0 = max(2, (n // 2) - 2)
	cy1 = cy0 + 3
	cactus_mod.cactus_set_region(cx0, cx1, cy0, cy1)

def try_unlocks():
	if (get_tick_count() % 2000) == 0:
		unlock(Unlocks.Speed)
		unlock(Unlocks.Watering)
		unlock(Unlocks.Expand)
		unlock(Unlocks.Sunflowers)
		unlock(Unlocks.Trees)
		unlock(Unlocks.Pumpkins)
		unlock(Unlocks.Cactus)
		unlock(Unlocks.Mazes)

def decide_target(x, y, n, carrot_emg, power_low, hay_low, wood_low, right_to_pumpkin):
	if cactus_mod.cactus_in_region(x, y):
		return Entities.Cactus

	left_col    = (x == 0)
	left_2_col  = (x == 1)
	right_col   = (x == n - 1)
	tree_col2   = (x == n - 3)
	top_band    = (y == n - 1) and (x >= 1 and x <= n - 2)
	bottom_band = (y == 0) and (x >= 1 and x <= n - 2)
	mid_band    = (y == (n // 2)) and (x >= 1 and x <= n - 2)
	grass_band  = (y == 1) and (x >= 1 and x <= n - 2)

	if left_col or (carrot_emg and left_2_col):
		return Entities.Carrot
	if top_band or bottom_band or (power_low and mid_band):
		return Entities.Sunflower
	if right_col or (tree_col2 and wood_low and not carrot_emg):
		if right_to_pumpkin and right_col:
			return Entities.Pumpkin
		if (y % 2) == (x % 2):
			return Entities.Tree
		else:
			return Entities.Grass
	if hay_low and grass_band:
		return Entities.Grass
	return Entities.Pumpkin

def run_game_logic(STRATEGY_PARAMS):
	CARROT_EMG = STRATEGY_PARAMS['CARROT_EMG']
	POWER_LOW = STRATEGY_PARAMS['POWER_LOW']
	HAY_LOW = STRATEGY_PARAMS['HAY_LOW']
	WOOD_LOW = STRATEGY_PARAMS['WOOD_LOW']
	RIGHT_PUM_H = STRATEGY_PARAMS['RIGHT_PUM_H']
	RIGHT_PUM_W = STRATEGY_PARAMS['RIGHT_PUM_W']
	F_MIN_STOCK = STRATEGY_PARAMS['F_MIN_STOCK']
	F_PUM_SPARSE_MOD = STRATEGY_PARAMS['F_PUM_SPARSE_MOD']
	F_PUM_WLOW_BIAS = STRATEGY_PARAMS['F_PUM_WLOW_BIAS']
	F_CAR_EMG_MOD = STRATEGY_PARAMS['F_CAR_EMG_MOD']

	init_game()
	cycle_start = get_time()
	grow_secs = config.GROW_SECS_DEFAULT
	
	while True:
		if IS_TRAINING_SIMULATION:
			if get_tick_count() > learning_mod.SIMULATION_TICKS:
				score = (num_items(Items.Carrot) * 1.0) + (num_items(Items.Pumpkin) * 1.5) + (num_items(Items.Wood) * 0.8) + (num_items(Items.Hay) * 0.5) + (num_items(Items.Cactus) * 2.0)
				quick_print("FINAL_SCORE:", score)
				return
		
		n = get_world_size()
		elapsed = get_time() - cycle_start
		water0  = num_items(Items.Water)
		if elapsed < 0.1:
			if water0 > 140: 
				grow_secs = 4.0
			elif water0 > 80: 
				grow_secs = 4.8
			else: 
				grow_secs = 5.8
		harvest_phase = (elapsed >= grow_secs)

		try_unlocks()
		
		power0  = num_items(Items.Power)
		carrot0 = num_items(Items.Carrot)
		hay0    = num_items(Items.Hay)
		wood0   = num_items(Items.Wood)
		fert0   = num_items(Items.Fertilizer)

		carrot_emg = (carrot0 < CARROT_EMG)
		power_low  = (power0  < POWER_LOW)
		hay_low    = (hay0    < HAY_LOW)
		wood_low   = (wood0   < WOOD_LOW)
		right_to_pumpkin = (hay0 > RIGHT_PUM_H) and (wood0 > RIGHT_PUM_W) and not carrot_emg

		sun_mod.sun_reset()
		cactus_mod.cactus_reset_round()
		farm_util.reset_fert_counts()
		job_heap = planner.heap_new()

		y = 0
		while y < n:
			x_start, x_end, x_step = (0, n, 1)
			if y % 2 != 0: 
				x_start, x_end, x_step = (n - 1, -1, -1)
			x = x_start
			while x != x_end:
				farm_util.move_to(x,y)
				is_sun_band = ((y == n-1 or y == 0) and (x >= 1 and x <= n-2)) or (power_low and y == (n//2) and (x >= 1 and x <= n-2))
				index_mod.update_cell_cache(x, y, is_sun_band)
				target = decide_target(x, y, n, carrot_emg, power_low, hay_low, wood_low, right_to_pumpkin)
				et_cached = index_mod.get_entity_cached(x, y)
				gd_cached = index_mod.get_ground_cached(x, y)
				if can_harvest():
					if et_cached != Entities.Sunflower and et_cached != Entities.Cactus:
						if not (et_cached == Entities.Pumpkin and not harvest_phase):
							planner.enqueue_harvest(job_heap, x, y, 10)
				if et_cached == Entities.Dead_Pumpkin:
					planner.enqueue_plant(job_heap, x, y, Entities.Pumpkin, 20)
				elif ((farm_util.needs_soil(target) and (gd_cached != Grounds.Soil or et_cached != target)) or (target == Entities.Grass and (gd_cached != Grounds.Grassland or et_cached != target)) or (target == Entities.Tree and et_cached != target) ):
					planner.enqueue_plant(job_heap, x, y, target, 25)
				if is_sun_band and et_cached == Entities.Sunflower:
					p = index_mod.get_petal_cached(x, y)
					if p != -1: 
						sun_mod.sun_observe(x, y, p)
				cactus_mod.cactus_process_cell(x, y)
				wt_cached = index_mod.get_water_cached(x,y)
				
				if is_sun_band and water0 > 30 and et_cached == Entities.Sunflower:
					th, md = (0,0)
					if power_low: 
						th, md = config.W_SUN_POWER_LOW
					elif water0 > 140: 
						th, md = config.W_SUN_H
					elif water0 > 90: 
						th, md = config.W_SUN_M
					else: 
						th, md = config.W_SUN_L
					if wt_cached < th: 
						planner.enqueue_water(job_heap, x, y, th, md, 40)
				elif target == Entities.Pumpkin and water0 > 40:
					th, md = (0,0)
					if water0 > 120: 
						th, md = config.W_PUM_H
					else: 
						th, md = config.W_PUM_L
					if wt_cached < th: 
						planner.enqueue_water(job_heap, x, y, th, md, 60)
				elif carrot_emg and target == Entities.Carrot and water0 > 20:
					th, md = config.W_CAR_EMG
					if wt_cached < th: 
						planner.enqueue_water(job_heap, x, y, th, md, 50)
				elif wood0 == 0 and target == Entities.Tree and water0 > 15:
					th, md = config.W_TREE_BOOT
					if wt_cached < th: 
						planner.enqueue_water(job_heap, x, y, th, md, 55)

				if fert0 > 0 and not can_harvest():
					if carrot_emg and target == Entities.Carrot and (get_tick_count() + x + 3*y) % F_CAR_EMG_MOD == 0:
						planner.enqueue_fertilize(job_heap, x, y, 70)
					elif target == Entities.Pumpkin and fert0 > F_MIN_STOCK:
						if wt_cached < F_PUM_WLOW_BIAS or harvest_phase:
							if (get_tick_count() + 2*x + y) % F_PUM_SPARSE_MOD == 0:
								planner.enqueue_fertilize(job_heap, x, y, 75)
				x = x + x_step
			y = y + 1

		if cactus_mod.cactus_finish_round():
			cactus_mod.cactus_maybe_mass_harvest()
		
		sun_targets = sun_mod.sun_targets_sorted(n)
		i = 0
		while i < len(sun_targets):
			tx, ty = sun_targets[i]
			farm_util.move_to(tx, ty)
			if can_harvest():
				if power0 < POWER_LOW + 20:
					harvest()
				else:
					p_now = measure()
					if p_now != None and p_now == sun_mod.sun_max_petal:
						harvest()
			i = i + 1

		planner.planner_run_all(job_heap)

		if harvest_phase:
			y = 0
			while y < n:
				x_start, x_end, x_step = (0, n, 1)
				if y % 2 != 0: 
					x_start, x_end, x_step = (n - 1, -1, -1)
				x = x_start
				while x != x_end:
					farm_util.move_to(x,y)
					if get_entity_type() == Entities.Pumpkin and can_harvest():
						harvest()
						farm_util.ensure_ground_for(Entities.Pumpkin)
						plant(Entities.Pumpkin)
					x = x + x_step
				y = y + 1
			cycle_start = get_time()