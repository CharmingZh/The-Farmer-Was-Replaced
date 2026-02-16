# 简易优先队列（小顶堆）+ 蛇形排序工具 + LRU（可选）

def heap_new():
	return []

def heap_push(h, item):
	h.append(item)
	i = len(h) - 1
	while i > 0:
		p = (i - 1) // 2
		if h[p][0] <= h[i][0]:
			break
		tmp = h[p]
		h[p] = h[i]
		h[i] = tmp
		i = p

def heap_pop(h):
	n = len(h)
	if n == 0:
		return None
	res = h[0]
	last = h.pop()
	if n > 1:
		h[0] = last
		i = 0
		while True:
			l = 2 * i + 1
			r = l + 1
			m = i
			if l < len(h):
				if h[l][0] < h[m][0]:
					m = l
			if r < len(h):
				if h[r][0] < h[m][0]:
					m = r
			if m == i:
				break
			tmp = h[i]
			h[i] = h[m]
			h[m] = tmp
			i = m
	return res

def snake_key(x, y, n):
	# 按蛇形顺序排序：y 递增，奇偶行反转 x
	if (y % 2) == 0:
		return y * n + x
	else:
		return y * n + (n - 1 - x)
