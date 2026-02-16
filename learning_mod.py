# =================================================================
#               --- 学习算法模块 ---
#
#   包含遗传算法的实现和所有与学习相关的配置。
# =================================================================

# --- 模式切换 ---
TRAINING_MODE = True # 改为 True 启动学习/训练模式

# --- 遗传算法参数 ---
POPULATION_SIZE = 100
GENERATIONS = 100
MUTATION_RATE = 0.1
MUTATION_STRENGTH = 0.2
TOURNAMENT_SIZE = 3
SIMULATION_TICKS = 200000

# --- 将训练找到的最佳策略粘贴到此处 ---
BEST_STRATEGY_HARDCODED = {'CARROT_EMG':290,'POWER_LOW':73,'HAY_LOW':425,'WOOD_LOW':754,'RIGHT_PUM_H':925,'RIGHT_PUM_W':959,'F_MIN_STOCK':76,'F_PUM_SPARSE_MOD':25,'F_PUM_WLOW_BIAS':0.5,'F_CAR_EMG_MOD':14}

# --- 定义可被优化的参数及其范围 ---
TUNABLE_PARAMS = {
	'CARROT_EMG': (150, 400, True),
	'POWER_LOW': (50, 150, True),
	'HAY_LOW': (400, 800, True),
	'WOOD_LOW': (600, 1000, True),
	'RIGHT_PUM_H': (500, 1000, True),
	'RIGHT_PUM_W': (700, 1200, True),
	'F_MIN_STOCK': (20, 100, True),
	'F_PUM_SPARSE_MOD': (15, 30, True),
	'F_PUM_WLOW_BIAS': (0.2, 0.6, False),
	'F_CAR_EMG_MOD': (5, 15, True)
}

# --- 手动定义的键列表 (为修复 .keys() 报错) ---
TUNABLE_PARAM_NAMES = [
	'CARROT_EMG', 'POWER_LOW', 'HAY_LOW', 'WOOD_LOW',
	'RIGHT_PUM_H', 'RIGHT_PUM_W', 'F_MIN_STOCK',
	'F_PUM_SPARSE_MOD', 'F_PUM_WLOW_BIAS', 'F_CAR_EMG_MOD'
]

# --- 遗传算法实现 ---
def ga_create_individual():
	individual = {}
	i = 0
	while i < len(TUNABLE_PARAM_NAMES):
		name = TUNABLE_PARAM_NAMES[i]
		bounds = TUNABLE_PARAMS[name]
		min_val, max_val, is_int = bounds
		val = random() * (max_val - min_val) + min_val
		if is_int:
			val = val // 1
		individual[name] = val
		i = i + 1
	return individual

def ga_create_population():
	population = []
	i = 0
	while i < POPULATION_SIZE:
		population.append(ga_create_individual())
		i = i + 1
	return population

def ga_run_simulation_for_evaluation(strategy_params):
	sim_unlocks = Unlocks
	sim_items = {Items.Carrot: 500, Items.Wood: 1000, Items.Hay: 1000}
	sim_globals = {
		'IS_TRAINING_SIMULATION': True,
		'STRATEGY_PARAMS': strategy_params
	}
	simulate("main", sim_unlocks, sim_items, sim_globals, random() * 1000, 256)

def run_training_session():
	# --- 此处已添加解锁 ---
	quick_print("Attempting to unlock Simulation module for training...")
	unlock(Unlocks.Simulation)
	
	quick_print("Initializing Genetic Algorithm Training...")
	population = ga_create_population()
	
	quick_print("===== GENERATION 1 of", GENERATIONS, "=====")
	quick_print("Launching simulations for the first generation.")
	quick_print("Please watch the console and manually record the FINAL_SCORE for each individual.")

	i = 0
	while i < len(population):
		quick_print("--- Launching Individual", i, "---")
		quick_print(population[i])
		ga_run_simulation_for_evaluation(population[i])
		i = i + 1
	
	quick_print("===== End of Generation 1 Simulations =====")
	quick_print("MANUAL STEP REQUIRED: All simulations for the first generation have been launched.")
	quick_print("Please review the console log, record all scores in order, and then manually create the next generation of strategies to test.")
	quick_print("This script has completed its automated task.")