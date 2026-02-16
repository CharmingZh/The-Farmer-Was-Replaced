from utils import *
from companion import *

def harvest_all_loop():
	# """循环收获所有可收获的作物"""
	while True:
		move_to_beyond(0, 0)
		for i in range(get_world_size()):
			for j in range(get_world_size()):
				if can_harvest():
					harvest()
				move_robot()

def harvest_all(time):
	# """收获所有可收获的作物time次"""
	for i in range(time):
		move_to_beyond(0, 0)
		for i in range(get_world_size()):
			for j in range(get_world_size()):
				if can_harvest():
					harvest()
				move_robot()

def harvest_by_line(time, line_num):
	# """按行收获所有可收获的作物time次，每次收获line_num行"""
	for i in range(time):
		move_to_beyond(0, 0)
		for i in range(line_num):
			for j in range(get_world_size()):
				if can_harvest():
					harvest()
				move_robot()

def gain_pumpkin(threhold=0):
	# """获得指定数量的南瓜"""
	if num_items(Items.Pumpkin) > threhold:
		return
	pumpkin_teck = 128

	farm_size = get_world_size()
	pum_borkens = []
	pumpkin_get_turn = (threhold-num_items(Items.Pumpkin)) / (farm_size * farm_size * 6 * pumpkin_teck)
	if pumpkin_get_turn < 0:
		pumpkin_get_turn = 1
	carrot_threhold = get_cost(Entities.Pumpkin)[Items.Carrot] * farm_size * farm_size * 1.3 * pumpkin_get_turn

	while num_items(Items.Pumpkin) < threhold:
		check_power()
		check_carrot(carrot_threhold)
		move_to_beyond(0,0)
		for i in range(get_world_size()):
			for j in range(get_world_size()):
				if get_ground_type() == Grounds.Grassland:
					till()
				if get_entity_type() != Entities.Pumpkin:
					if(can_harvest()):
						harvest()
					plant(Entities.Pumpkin)
				move_robot()
		move_to_beyond(0,0)
		for i in range(get_world_size()):
			for j in range(get_world_size()):
				if not can_harvest():
					pum_borkens.append([get_pos_x(),get_pos_y()])
					if get_entity_type() != Entities.Pumpkin:
						plant(Entities.Pumpkin)
				move_robot()
		while len(pum_borkens) != 0:
			pum_broken_tem = []
			for i in range(len(pum_borkens)):
				move_to_beyond(pum_borkens[0][0], pum_borkens[0][1])
				pum_borkens.pop(0)
				if not can_harvest():
					pum_broken_tem.append([get_pos_x(),get_pos_y()])
					if get_entity_type() != Entities.Pumpkin:
						plant(Entities.Pumpkin)
						check_water()
			pum_borkens = get_shortest_path(pum_broken_tem)
		harvest()

def gain_power(threhold = 4000):
	# """获得指定数量的能量"""
	while num_items(Items.Power) < threhold:
		sun_data = []
		for i in range(9):
			sun_data.append([])
		move_to_beyond(0, 0)
		for j in range(get_world_size()):
			for i in range(get_world_size()):
				if can_harvest():
					harvest()
				check_entities(Entities.Sunflower)
				index = measure() - 7
				if index%2 == 0:
					sun_data[index].insert(len(sun_data[index]),(get_pos_x(),get_pos_y()))
				else:
					sun_data[index].insert(0, (get_pos_x(),get_pos_y()))
				move_robot()

		for i in range(8, -1, -1):
			for j in range(len(sun_data[i])):
				(x,y) = sun_data[i][0]
				move_to_beyond(x,y)
				harvest()
				sun_data[i].pop(0)

def gain_weird(threhold=400000):
	# """获得指定数量的怪异物质"""
	farm_map = dict()
	move_to_beyond(5,5)
	if(can_harvest()):
		harvest()
	check_entities(Entities.Grass)

	while num_items(Items.Weird_Substance) < threhold:
		e_type,(x,y) = get_companion()
		if (x,y) not in farm_map or farm_map[(x,y)] != e_type:
			move_to_beyond(x,y)
			if(can_harvest()):
				harvest()
			else:
				till()
			check_entities(e_type)
			farm_map[(x,y)]=e_type
		move_to_beyond(5,5)
		use_item(Items.Fertilizer)
		while True:
			if(can_harvest()):
				harvest()
				break

def gain_carrot(threhold = 4000000):
	# """获得指定数量的胡萝卜"""
	gain_companion(0,0,threhold)

def gain_wood(threhold = 0):
	# """获得指定数量的木材"""
	gain_companion(0,threhold,0)

def gain_hay(threhold = 0):
	# """获得指定数量的干草"""
	gain_companion(threhold,0,0)

def check(item, threhold, default_threhold, func):
	# """检查指定物品数量是否达到阈值，若未达到则调用相应函数获取该物品
	# 	item: 要检查的物品
	# 	threhold: 目标阈值
	# 	default_threhold: 默认阈值
	# 	func: 获取物品的函数
	# """
	if num_items(item) < threhold:
		if threhold > default_threhold:
			func(threhold)
		else:
			func()

def check_power(threhold=500):
	# """检查能量数量是否达到阈值，若未达到则获取能量"""
	check(Items.Power, threhold, 500, gain_power)

def check_weird(threhold=10000):
	# """检查怪异物质数量是否达到阈值，若未达到则获取怪异物质"""
	check(Items.Weird_Substance, threhold, 10000, gain_weird)

def check_wood(threhold=10000):
	# """检查木材数量是否达到阈值，若未达到则获取木材"""
	check(Items.Wood, threhold, 0, gain_wood)

def check_hay(threhold=10000):
	# """检查干草数量是否达到阈值，若未达到则获取干草"""
	check(Items.Hay, threhold, 0, gain_hay)

def check_carrot(threhold=10000):
	# """检查胡萝卜数量是否达到阈值，若未达到则获取胡萝卜"""
	check(Items.Carrot, threhold, 4000000, gain_carrot)

def check_pumpkin(threhold=10000):
	# """检查南瓜数量是否达到阈值，若未达到则获取南瓜"""
	check(Items.Pumpkin, threhold, 0, gain_pumpkin)

def check_power(threhold=500):
	# """检查能量数量是否达到阈值，若未达到则获取能量"""
	check(Items.Power, threhold, 2000, gain_power)

if __name__ == "__main__":
	# op_gain_power(999999999)
	# gain_weird(999999999)
	#gain_carrot(450000)
	gain_pumpkin(999999999)