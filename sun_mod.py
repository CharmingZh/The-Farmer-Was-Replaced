# 向日葵最大花瓣索引：只收最大值坐标集合，避免整带反复空扫

from structs import snake_key

max_petal = 7
max_set = set()

def reset():
	global max_petal
	global max_set
	max_petal = 7
	max_set = set()

def observe(x, y, p):
	global max_petal
	global max_set
	if p > max_petal:
		max_petal = p
		max_set = set()
		max_set.add((x, y))
	else:
		if p == max_petal:
			max_set.add((x, y))

def targets_sorted(n):
	# 蛇形排序，走线更短
	lst = []
	for t in max_set:
		lst.append(t)
	# 简易冒泡
	m = len(lst)
	for i in range(m):
		for j in range(m - 1):
			a = snake_key(lst[j][0], lst[j][1], n)
			b = snake_key(lst[j+1][0], lst[j+1][1], n)
			if a > b:
				tmp = lst[j]
				lst[j] = lst[j+1]
				lst[j+1] = tmp
	return lst
	