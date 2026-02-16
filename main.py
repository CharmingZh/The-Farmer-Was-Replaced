# =================================================================
#               --- 主程序入口 ---
#
#   负责根据模式选择，启动训练或执行最优策略。
# =================================================================

import learning_mod
import game_logic

# --- 状态预定义 (用于兼容不支持 globals() 的环境) ---
# 这些变量会被 simulate() 函数动态覆盖
IS_TRAINING_SIMULATION = False
STRATEGY_PARAMS = {}

# --- 主执行入口 ---
clear()

if IS_TRAINING_SIMULATION:
	# 如果是通过 simulate() 启动的，并且注入了训练标志
	# 则直接运行游戏逻辑，使用注入的策略参数
	game_logic.run_game_logic(STRATEGY_PARAMS)
else:
	# 否则，这是正常启动
	if learning_mod.TRAINING_MODE:
		# 运行遗传算法训练会话
		learning_mod.run_training_session()
	else:
		# 使用我们预设的最佳策略来正常玩游戏
		quick_print("Executing with best strategy...")
		game_logic.run_game_logic(learning_mod.BEST_STRATEGY_HARDCODED)