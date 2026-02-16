# 基础工具 + 手工容器 + 路径/地面/浇水

def in_range(x, a, b):
	return (x >= a) and (x <= b)

def needs_soil(entity):
	return (entity == Entities.Pumpkin) or (entity == Entities.Carrot) or (entity == Entities.Sunflower) or (entity == Entities.Cactus)

def ensure_ground_for(entity):
	g = get_ground_type()
	if needs_soil(entity):
		if g != Grounds.Soil:
			till()
	else:
		if entity == Entities.Grass:
			if g != Grounds.Grassland:
				till()

def plant_if_needed(entity):
	if get_entity_type() != entity:
		plant(entity)

# 稀疏浇水：避免瞬时清空水仓
def water_sparse(threshold, mod):
	if get_water() < threshold:
		k = get_pos_x() + get_pos_y() + get_tick_count()
		if (k % mod) == 0:
			use_item(Items.Water)

# 坐标与移动
def move_to(tx, ty):
	# 横向优先，再纵向；保证可复用
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

# 手工队列/栈（列表做，带头指针）
def make_queue():
	return [[], 0]  # [list, head]

def q_push(q, item):
	q[0].append(item)

def q_pop(q):
	i = q[1]
	if i < len(q[0]):
		item = q[0][i]
		q[1] = i + 1
		return item
	return None

def q_empty(q):
	return q[1] >= len(q[0])

def make_stack():
	return []

def s_push(s, item):
	s.append(item)

def s_pop(s):
	if len(s) > 0:
		return s.pop()
	return None
