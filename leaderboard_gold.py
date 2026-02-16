# =================================================================
#  两个 4×4 迷宫 · 左下角对齐（中心=左下角+(2,2)）·主机占右上角
#  - A_LL=(1,1)  B_LL=(6,1)
#  - 复用节奏：脚下宝箱时 299 次 use_item(动态 need) + 第 300 次 harvest
#  - 锚点：无迷宫时先补种灌木再重建；重建后用 measure() 验证成功
#  - 主机=第 32 格，站 B 的右上角，不再移动
#  - 逐行语句，无分号、无推导、无 lambda、无 .get()
# =================================================================

def move_to(tx, ty):
	px = get_pos_x()
	py = get_pos_y()
	while px < tx:
		move(East)
		px = px + 1
	while px > tx:
		move(West)
		px = px - 1
	while py < ty:
		move(North)
		py = py + 1
	while py > ty:
		move(South)
		py = py - 1
	return None

def current_need_for_side(side_len):
	lv = num_unlocked(Unlocks.Mazes)
	if lv < 1:
		lv = 1
	p = 1
	i = 1
	while i < lv:
		p = p * 2
		i = i + 1
	return side_len * p

# ------------------- 普通守位子机：299复用 + 第300收 -------------------
def sentry_worker_here():
	wx = get_pos_x()
	wy = get_pos_y()
	side = 4
	cycle = 0
	round_id = 1
	quick_print("SENTRY_START", wx, wy, "round", round_id, "", "", "")
	while True:
		g = measure()
		if g != None:
			if g[0] == wx and g[1] == wy:
				need = current_need_for_side(side)
				if cycle < 299:
					have = num_items(Items.Weird_Substance)
					if have >= need:
						use_item(Items.Weird_Substance, need)
						cycle = cycle + 1
						if cycle % 50 == 0:
							quick_print("SENTRY_REUSE", wx, wy, "cycle", cycle, "need", need, "")
					else:
						quick_print("SENTRY_WAIT_WEIRD", wx, wy, "have", have, "need", need, "")
				else:
					harvest()
					quick_print("SENTRY_HARVEST_300", wx, wy, "round", round_id, "", "", "")
					cycle = 0
					round_id = round_id + 1
	return None

# ------------------- 锚点子机：创建/复用/收获/重建（自动补种 + 动态 need） -------------------
def anchor_cycler_worker_here():
	cx = get_pos_x()
	cy = get_pos_y()
	side = 4
	cycle = 0
	round_id = 1
	quick_print("ANCHOR_START", cx, cy, "round", round_id, "", "", "")

	# 等 31 台子机就位（主机占第 32 格）
	while num_drones() < max_drones() - 1:
		g0 = measure()
		if g0 != None:
			if g0[0] == cx and g0[1] == cy:
				need0 = current_need_for_side(side)
				if cycle < 299:
					have0 = num_items(Items.Weird_Substance)
					if have0 >= need0:
						use_item(Items.Weird_Substance, need0)
						cycle = cycle + 1
				else:
					harvest()
					quick_print("ANCHOR_EARLY_HARV_BEFORE_FULL", cx, cy, "round", round_id, "", "", "")
					cycle = 0
					round_id = round_id + 1

	# 初始化：若没有迷宫，种灌木并创建（动态 need）
	if measure() == None:
		if get_entity_type() != Entities.Bush:
			if get_ground_type() != Grounds.Soil:
				till()
			plant(Entities.Bush)
			quick_print("ANCHOR_PLANT_BUSH", cx, cy, "", "", "", "", "")
		need_i = current_need_for_side(side)
		have_i = num_items(Items.Weird_Substance)
		if have_i >= need_i:
			use_item(Items.Weird_Substance, need_i)
			if measure() != None:
				quick_print("ANCHOR_INIT_MAZE_OK", cx, cy, "need", need_i, "", "", "")
			else:
				quick_print("ANCHOR_INIT_MAZE_FAIL", cx, cy, "need", need_i, "have", have_i, "")
		else:
			quick_print("ANCHOR_INIT_WAIT_WEIRD", cx, cy, "have", have_i, "need", need_i, "")

	# 长期循环：无迷宫→补种+重建，有迷宫→复用节拍
	while True:
		g = measure()
		if g == None:
			# 上一轮第 300 次被收走或首次未建成 → 先确保脚下有灌木
			if get_entity_type() != Entities.Bush:
				if get_ground_type() != Grounds.Soil:
					till()
				plant(Entities.Bush)
				quick_print("ANCHOR_REPLANT_BUSH", cx, cy, "", "", "", "", "")
			need_r = current_need_for_side(side)
			have_r = num_items(Items.Weird_Substance)
			if have_r >= need_r:
				use_item(Items.Weird_Substance, need_r)
				if measure() != None:
					round_id = round_id + 1
					cycle = 0
					quick_print("ANCHOR_REBUILD_OK", cx, cy, "round", round_id, "need", need_r, "")
				else:
					quick_print("ANCHOR_REBUILD_FAIL_AFTER_PLANT", cx, cy, "need", need_r, "have", have_r, "")
			else:
				quick_print("ANCHOR_REBUILD_WAIT_WEIRD", cx, cy, "have", have_r, "need", need_r, "")
		else:
			if g[0] == cx and g[1] == cy:
				need_u = current_need_for_side(side)
				if cycle < 299:
					have_u = num_items(Items.Weird_Substance)
					if have_u >= need_u:
						use_item(Items.Weird_Substance, need_u)
						cycle = cycle + 1
						if cycle % 50 == 0:
							quick_print("ANCHOR_REUSE", cx, cy, "cycle", cycle, "need", need_u, "")
					else:
						quick_print("ANCHOR_REUSE_WAIT_WEIRD", cx, cy, "have", have_u, "need", need_u, "")
				else:
					harvest()
					quick_print("ANCHOR_HARVEST_300", cx, cy, "round", round_id, "", "", "")
					cycle = 0
	return None

# ------------------- 两个 4×4 的左下角 -------------------
def layout_two_mazes_LL():
	llAx = 1
	llAy = 1
	llBx = 6
	llBy = 1
	return (llAx, llAy, llBx, llBy)

# 在 [LL..LL+3]×[LL..LL+3] 逐格派：锚点=LL+(2,2)，跳过“B的右上角”留给主机
def deploy_grid_from_LL_skip_RU_for_main(llx, lly, skip_ru, max_to_spawn, used_ref, anchor_used_ref):
	count = 0
	anchor_used = 0
	anchor_x = llx + 2
	anchor_y = lly + 2
	ru_x = llx + 3
	ru_y = lly + 3
	y = lly
	while y <= lly + 3 and count < max_to_spawn:
		x = llx
		while x <= llx + 3 and count < max_to_spawn:
			if skip_ru == 1 and x == ru_x and y == ru_y:
				quick_print("SKIP_RU_FOR_MAIN", x, y, "", "", "", "", "")
			else:
				move_to(x, y)
				if num_drones() < max_drones():
					if x == anchor_x and y == anchor_y and anchor_used == 0:
						ok = spawn_drone(anchor_cycler_worker_here)
						if ok:
							count = count + 1
							anchor_used = 1
							quick_print("DEPLOY_ANCHOR", x, y, "count", count, "", "", "")
					else:
						ok2 = spawn_drone(sentry_worker_here)
						if ok2:
							count = count + 1
							if count % 4 == 0:
								quick_print("DEPLOY_SENTRY", x, y, "count", count, "", "", "")
			x = x + 1
		y = y + 1
	used_ref[0] = count
	anchor_used_ref[0] = anchor_used
	return None

# ------------------- 主机就位后执行“守位循环”（动态 need） -------------------
def main_sentry_loop_at(wx, wy):
	side = 4
	cycle = 0
	round_id = 1
	quick_print("MAIN_TAKE_RU", wx, wy, "round", round_id, "", "", "")
	while True:
		g = measure()
		if g != None:
			if g[0] == wx and g[1] == wy:
				need = current_need_for_side(side)
				if cycle < 299:
					have = num_items(Items.Weird_Substance)
					if have >= need:
						use_item(Items.Weird_Substance, need)
						cycle = cycle + 1
						if cycle % 50 == 0:
							quick_print("MAIN_REUSE", wx, wy, "cycle", cycle, "need", need, "")
					else:
						quick_print("MAIN_WAIT_WEIRD", wx, wy, "have", have, "need", need, "")
				else:
					harvest()
					quick_print("MAIN_HARVEST_300", wx, wy, "round", round_id, "", "", "")
					cycle = 0
					round_id = round_id + 1
	return None

def main():
	set_execution_speed(0)
	if num_unlocked(Unlocks.Costs) == 0:
		unlock(Unlocks.Costs)
	if num_unlocked(Unlocks.Mazes) == 0:
		unlock(Unlocks.Mazes)

	llAx, llAy, llBx, llBy = layout_two_mazes_LL()
	quick_print("LAYOUT_LL", "A_LL", llAx, llAy, "B_LL", llBx, llBy, "")

	total_slots = max_drones()
	if total_slots < 1:
		quick_print("ERROR", "NO_DRONE_SLOTS", "", "", "", "", "", "")
		return None

	# 派出 31 台子机，B 的右上角留给主机
	need_sub = 31
	if need_sub > total_slots:
		need_sub = total_slots

	remain = need_sub
	usedA = [0]
	ancA = [0]
	targetA = 16
	if remain < targetA:
		targetA = remain
	deploy_grid_from_LL_skip_RU_for_main(llAx, llAy, 0, targetA, usedA, ancA)
	remain = remain - usedA[0]
	quick_print("A_DEPLOYED", usedA[0], "ANCHOR_A", ancA[0], "REMAIN_FOR_SUB", remain, "", "", "")

	usedB = [0]
	ancB = [0]
	if remain > 0:
		targetB = 15
		if remain < targetB:
			targetB = remain
		deploy_grid_from_LL_skip_RU_for_main(llBx, llBy, 1, targetB, usedB, ancB)
		remain = remain - usedB[0]
	quick_print("B_DEPLOYED", usedB[0], "ANCHOR_B", ancB[0], "REMAIN_FOR_SUB", remain, "", "", "")

	quick_print("DISPATCH_SUM", "subs", usedA[0] + usedB[0], "cur_num_drones", num_drones(), "max", max_drones(), "", "")

	# 主机去占 B 的右上角并进入守位循环
	main_ru_x = llBx + 3
	main_ru_y = llBy + 3
	move_to(main_ru_x, main_ru_y)
	quick_print("MAIN_MOVE_TO_RU", main_ru_x, main_ru_y, "num_drones", num_drones(), "", "", "")

	return main_sentry_loop_at(main_ru_x, main_ru_y)

main()
