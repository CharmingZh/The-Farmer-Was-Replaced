# =========================================================
#  Snake Trainer v3（线性 Q-learning · 仅训练）
#  - 不含 simulate()；直接运行本文件开始训练
#  - 训练结束打印权重：BEGIN_WEIGHTS ... END_WEIGHTS
#  - 与 v1.4 吃法对齐：到达苹果格 → 再离开一步完成吃；吃步不弹尾
#  - 加入：活性校验、允许走进尾末(非吃步)、安全吃脚下苹果、追尾兜底
# =========================================================

# ---------- 训练参数 ----------
WORLD_SIZE = 32
MAX_STEPS_PER_EP = 4000
EPISODES = 200
ALPHA = 0.15
GAMMA = 0.98
EPS_START = 0.25
EPS_MIN = 0.02
EPS_DECAY_EVERY = 10
EPS_DECAY_FACTOR = 0.92
STEP_PENALTY = -0.01
EAT_REWARD = 1.00
DEAD_PENALTY = -1.00
PRINT_EVERY = 5
EXEC_SPEED = 8

# ---------- 通用工具 ----------
def get_next_pos(px, py, direction):
	if direction == North:
		return (px, py + 1)
	if direction == South:
		return (px, py - 1)
	if direction == East:
		return (px + 1, py)
	if direction == West:
		return (px - 1, py)
	return (px, py)

def in_bounds(x, y, n):
	if x < 0:
		return False
	if x >= n:
		return False
	if y < 0:
		return False
	if y >= n:
		return False
	return True

def neighbors(p):
	res = []
	res.append((p[0], p[1] + 1))
	res.append((p[0] + 1, p[1]))
	res.append((p[0], p[1] - 1))
	res.append((p[0] - 1, p[1]))
	return res

def is_safe_next(pos, tail, world_size, allow_tail_end):
	x = pos[0]
	y = pos[1]
	if x < 0 or x >= world_size or y < 0 or y >= world_size:
		return False
	i = 0
	while i < len(tail):
		if tail[i] == pos:
			if allow_tail_end == True and len(tail) > 0 and pos == tail[-1]:
				return True
			return False
		i = i + 1
	return True

def reachable(start, target, tail, world_size, allow_tail_end):
	ok = is_safe_next(start, tail, world_size, allow_tail_end)
	if ok != True:
		return False
	seen = set()
	q = []
	seen.add(start)
	q.append(start)
	found = False
	while len(q) > 0 and found != True:
		cur = q.pop(0)
		if cur == target:
			found = True
		else:
			nbs = neighbors(cur)
			i = 0
			while i < len(nbs):
				nb = nbs[i]
				if is_safe_next(nb, tail, world_size, allow_tail_end) == True:
					if nb not in seen:
						seen.add(nb)
						q.append(nb)
				i = i + 1
	return found

# ---------- 特征与线性 Q ----------
def actions_list():
	arr = []
	arr.append(North)
	arr.append(East)
	arr.append(South)
	arr.append(West)
	return arr

def manhattan(ax, ay, bx, by):
	dx = ax - bx
	if dx < 0:
		dx = 0 - dx
	dy = ay - by
	if dy < 0:
		dy = 0 - dy
	return dx + dy

def feature_vector(px, py, tail, n, ax, ay, direction):
	nxy = get_next_pos(px, py, direction)
	nx = nxy[0]
	ny = nxy[1]

	d_before = manhattan(px, py, ax, ay)
	d_after = manhattan(nx, ny, ax, ay)

	f0 = 0.0
	if in_bounds(nx, ny, n) == True:
		f0 = 0.0 - d_after
	else:
		f0 = -9999.0

	f1 = 0.0
	if is_safe_next((nx, ny), tail, n, True) == True:
		f1 = 1.0

	f2 = 0.0
	if ax > px and direction == East:
		f2 = 1.0
	else:
		if ax < px and direction == West:
			f2 = 1.0

	f3 = 0.0
	if ay > py and direction == North:
		f3 = 1.0
	else:
		if ay < py and direction == South:
			f3 = 1.0

	free_deg = 0.0
	if in_bounds(nx, ny, n) == True:
		if is_safe_next((nx, ny + 1), tail, n, True) == True:
			free_deg = free_deg + 1.0
		if is_safe_next((nx + 1, ny), tail, n, True) == True:
			free_deg = free_deg + 1.0
		if is_safe_next((nx, ny - 1), tail, n, True) == True:
			free_deg = free_deg + 1.0
		if is_safe_next((nx - 1, ny), tail, n, True) == True:
			free_deg = free_deg + 1.0
	f4 = free_deg / 4.0

	adx = ax - px
	if adx < 0:
		adx = 0 - adx
	ady = ay - py
	if ady < 0:
		ady = 0 - ady
	f5 = 0.0
	if adx >= ady:
		if direction == East or direction == West:
			f5 = 1.0
	else:
		if direction == North or direction == South:
			f5 = 1.0

	f6 = 0.0
	if d_after <= d_before:
		f6 = 1.0

	cx = (n - 1) / 2.0
	cy = (n - 1) / 2.0
	dc = manhattan(nx, ny, cx, cy)
	maxdc = manhattan(0, 0, cx, cy)
	if maxdc == 0:
		maxdc = 1
	f7 = 1.0 - (dc / maxdc)

	vec = []
	vec.append(f0)
	vec.append(f1)
	vec.append(f2)
	vec.append(f3)
	vec.append(f4)
	vec.append(f5)
	vec.append(f6)
	vec.append(f7)
	return vec

def dot_wf(W, F):
	s = 0.0
	i = 0
	while i < len(W):
		s = s + W[i] * F[i]
		i = i + 1
	return s

def pick_action_eps(px, py, tail, n, ax, ay, W, eps):
	acts = actions_list()

	r = random()
	if r < eps:
		k = random()
		if k < 0.25:
			return acts[0]
		if k < 0.50:
			return acts[1]
		if k < 0.75:
			return acts[2]
		return acts[3]

	best_a = acts[0]
	best_v = -9999999.0
	i = 0
	while i < len(acts):
		fi = feature_vector(px, py, tail, n, ax, ay, acts[i])
		qi = dot_wf(W, fi)
		if qi > best_v:
			best_v = qi
			best_a = acts[i]
		i = i + 1
	return best_a

def td_update(W, F, r, F_next_best):
	q_now = dot_wf(W, F)
	q_next = 0.0
	if F_next_best != None:
		q_next = dot_wf(W, F_next_best)
	y = r + GAMMA * q_next
	delta = y - q_now
	i = 0
	while i < len(W):
		W[i] = W[i] + ALPHA * delta * F[i]
		i = i + 1
	return W

# ---------- 安全吃“脚下苹果” ----------
def eat_underfoot_safely(tail, world_size):
	px = get_pos_x()
	py = get_pos_y()
	dirs = actions_list()
	i = 0
	while i < len(dirs):
		nxy = get_next_pos(px, py, dirs[i])
		if is_safe_next(nxy, tail, world_size, False) == True:
			ok = move(dirs[i])
			if ok == True:
				tail.insert(0, (px, py))
				return True
		i = i + 1
	return False

# ---------- 一步执行（带活性与尾巴规则） ----------
def step_once_choose_and_move(target_x, target_y, tail, n, W, eps):
	px = get_pos_x()
	py = get_pos_y()

	on_apple = False
	et = get_entity_type()
	if et != None:
		if et == Entities.Apple:
			on_apple = True

	act = pick_action_eps(px, py, tail, n, target_x, target_y, W, eps)
	next_pos = get_next_pos(px, py, act)

	allow_tail_end = True
	if on_apple == True:
		allow_tail_end = False

	if is_safe_next(next_pos, tail, n, allow_tail_end) != True:
		return False, False, True

	if on_apple == True:
		next_tail = []
		next_tail.append((px, py))
		i0 = 0
		while i0 < len(tail):
			next_tail.append(tail[i0])
			i0 = i0 + 1
		ok_conn = reachable(next_pos, next_tail[-1], next_tail, n, False)
	else:
		next_tail = []
		next_tail.append((px, py))
		i1 = 0
		while i1 < len(tail) - 1:
			next_tail.append(tail[i1])
			i1 = i1 + 1
		if len(tail) == 0:
			pass
		ok_conn = True
		if len(next_tail) > 0:
			ok_conn = reachable(next_pos, next_tail[-1], next_tail, n, True)

	if ok_conn != True:
		return False, False, True

	ok = move(act)
	if ok != True:
		return False, False, True

	tail.insert(0, (px, py))
	ate = False
	if on_apple == True:
		ate = True
	else:
		if len(tail) > 0:
			tail.pop()

	return True, ate, False

# ---------- 追尾兜底（当朝目标全失败时） ----------
def step_towards_tail(tail, world_size):
	if len(tail) == 0:
		return False
	px = get_pos_x()
	py = get_pos_y()
	tx = tail[-1][0]
	ty = tail[-1][1]
	cands = actions_list()
	best = None
	best_md = 9999999
	i = 0
	while i < len(cands):
		nxy = get_next_pos(px, py, cands[i])
		if is_safe_next(nxy, tail, world_size, True) == True:
			md = manhattan(nxy[0], nxy[1], tx, ty)
			if md < best_md:
				best_md = md
				best = cands[i]
		i = i + 1
	if best != None:
		return move(best)
	return False

# ---------- 单回合训练 ----------
def train_one_episode(W):
	set_world_size(WORLD_SIZE)
	change_hat(Hats.Dinosaur_Hat)
	tail = []
	steps = 0
	total_R = 0.0
	apples = 0

	ap = measure()
	if not ap:
		quick_print("ERROR", "no apple items")
		return total_R, steps, apples, W
	tx = ap[0]
	ty = ap[1]

	px0 = get_pos_x()
	py0 = get_pos_y()
	on0 = False
	et0 = get_entity_type()
	if et0 != None:
		if et0 == Entities.Apple:
			on0 = True
	if on0 == True:
		ok0 = eat_underfoot_safely(tail, WORLD_SIZE)
		if ok0 != True:
			return total_R, steps, apples, W
	else:
		d4 = actions_list()
		m0 = False
		j = 0
		while j < len(d4) and m0 != True:
			np0 = get_next_pos(px0, py0, d4[j])
			if is_safe_next(np0, tail, WORLD_SIZE, True) == True:
				if move(d4[j]) == True:
					tail.append((px0, py0))
					m0 = True
			j = j + 1
		if m0 != True:
			return total_R, steps, apples, W

	eps = EPS_START

	while steps < MAX_STEPS_PER_EP:
		px = get_pos_x()
		py = get_pos_y()

		if not (px == tx and py == ty):
			a_star = pick_action_eps(px, py, tail, WORLD_SIZE, tx, ty, W, 0.0)
			F_cur = feature_vector(px, py, tail, WORLD_SIZE, tx, ty, a_star)

			moved, ate, dead = step_once_choose_and_move(tx, ty, tail, WORLD_SIZE, W, eps)
			if moved != True and dead != True:
				ok_tail = step_towards_tail(tail, WORLD_SIZE)
				if ok_tail == True:
					moved = True
					dead = False

			r = STEP_PENALTY
			if dead == True:
				r = DEAD_PENALTY
				W = td_update(W, F_cur, r, None)
				total_R = total_R + r
				steps = steps + 1
				break
			else:
				if moved == True and ate == True:
					r = r + EAT_REWARD
					apples = apples + 1
					nxt = measure()
					if not nxt:
						W = td_update(W, F_cur, r, None)
						total_R = total_R + r
						steps = steps + 1
						break
					tx = nxt[0]
					ty = nxt[1]
					nx = get_pos_x()
					ny = get_pos_y()
					a2 = pick_action_eps(nx, ny, tail, WORLD_SIZE, tx, ty, W, 0.0)
					F_next = feature_vector(nx, ny, tail, WORLD_SIZE, tx, ty, a2)
					W = td_update(W, F_cur, r, F_next)
				else:
					nx2 = get_pos_x()
					ny2 = get_pos_y()
					a3 = pick_action_eps(nx2, ny2, tail, WORLD_SIZE, tx, ty, W, 0.0)
					F_next2 = feature_vector(nx2, ny2, tail, WORLD_SIZE, tx, ty, a3)
					W = td_update(W, F_cur, r, F_next2)
				total_R = total_R + r
				steps = steps + 1
		else:
			cands = actions_list()
			ch = None
			k = 0
			while k < len(cands) and ch == None:
				np1 = get_next_pos(px, py, cands[k])
				if is_safe_next(np1, tail, WORLD_SIZE, False) == True:
					ntail = []
					ntail.append((px, py))
					ti = 0
					while ti < len(tail):
						ntail.append(tail[ti])
						ti = ti + 1
					if reachable(np1, ntail[-1], ntail, WORLD_SIZE, False) == True:
						ch = cands[k]
				k = k + 1
			if ch == None:
				rb = DEAD_PENALTY
				Fx = feature_vector(px, py, tail, WORLD_SIZE, tx, ty, North)
				W = td_update(W, Fx, rb, None)
				total_R = total_R + rb
				steps = steps + 1
				break

			ok2 = move(ch)
			if ok2 != True:
				rb2 = DEAD_PENALTY
				Fy = feature_vector(px, py, tail, WORLD_SIZE, tx, ty, ch)
				W = td_update(W, Fy, rb2, None)
				total_R = total_R + rb2
				steps = steps + 1
				break

			tail.insert(0, (px, py))
			rgain = EAT_REWARD + STEP_PENALTY
			ap2 = measure()
			if not ap2:
				Fz = feature_vector(px, py, tail, WORLD_SIZE, tx, ty, ch)
				W = td_update(W, Fz, rgain, None)
				total_R = total_R + rgain
				steps = steps + 1
				break
			tx = ap2[0]
			ty = ap2[1]
			nx3 = get_pos_x()
			ny3 = get_pos_y()
			astar3 = pick_action_eps(nx3, ny3, tail, WORLD_SIZE, tx, ty, W, 0.0)
			Fnext3 = feature_vector(nx3, ny3, tail, WORLD_SIZE, tx, ty, astar3)
			Fcur3 = feature_vector(px, py, tail, WORLD_SIZE, tx, ty, ch)
			W = td_update(W, Fcur3, rgain, Fnext3)
			total_R = total_R + rgain
			steps = steps + 1

	return total_R, steps, apples, W

# ---------- 评估与输出 ----------
def rollout_with_weights(W, rounds):
	i = 0
	sumR = 0.0
	sumS = 0
	sumA = 0
	while i < rounds:
		R, T, A, _ = train_one_episode(W)
		sumR = sumR + R
		sumS = sumS + T
		sumA = sumA + A
		i = i + 1
	avgR = sumR / rounds
	avgS = sumS / rounds
	avgA = sumA / rounds
	return avgR, avgS, avgA

def print_weights(W):
	quick_print("BEGIN_WEIGHTS")
	i = 0
	while i < len(W):
		quick_print("W" + str(i) + "=", W[i])
		i = i + 1
	quick_print("END_WEIGHTS")
	return None

# ---------- 训练主流程 ----------
def main():
	set_execution_speed(EXEC_SPEED)
	set_world_size(WORLD_SIZE)
	change_hat(Hats.Dinosaur_Hat)

	# 自检：若没苹果物资，直接提示并退出
	ap = measure()
	if not ap:
		quick_print("ERROR", "No apple items. Provide Items.AppleSeed 或 Items.Apple.")
		return None

	W = []
	iw = 0
	while iw < 8:
		W.append(0.0)
		iw = iw + 1

	best = -9999999.0
	eps = EPS_START
	ep = 0
	while ep < EPISODES:
		R, T, A, W = train_one_episode(W)
		if ((ep + 1) % EPS_DECAY_EVERY) == 0:
			if eps > EPS_MIN:
				eps = eps * EPS_DECAY_FACTOR
				if eps < EPS_MIN:
					eps = EPS_MIN
		if R > best:
			best = R
		if (ep % PRINT_EVERY) == 0:
			quick_print("EP", ep, "R", R, "steps", T, "apples", A, "bestR", best)
		ep = ep + 1

	avgR, avgS, avgA = rollout_with_weights(W, 3)
	quick_print("EVAL", "avgR", avgR, "avgS", avgS, "avgA", avgA)
	print_weights(W)
	return None

main()
