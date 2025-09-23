# main.py
from core.logger import logger
from core.managers.strategy_manager import StrategyManager
from core.managers.platform_manager import PlatformManager
from core.services.order_service import place_order, build_order

def main():
    # 加载配置文件
    strategies_config = [
        {"strategy_name": "martingale_v3", "name": "Martingale Strategy", "params": {}}
    ]
    
    # 初始化策略管理器
    strategy_manager = StrategyManager(strategies_config)
    
    # 初始化平台管理器
    platform_manager = PlatformManager()

    # 获取平台实例（可以根据配置动态选择平台）
    binance = platform_manager.get_platform("binance")
    coinw = platform_manager.get_platform("coinw")
    okx = platform_manager.get_platform("okx")

    logger.log_info("🚀 启动完成，进入主循环")
    
    while True:
        # 获取所有活跃策略
        for strategy in strategy_manager.get_active_strategies():
            # 获取交易计划
            plan = strategy.decide()
            if plan:
                # 选择平台，假设我们选择了Binance
                platform = binance

                # 执行下单操作
                order_response = place_order(platform, build_order(strategy, plan))
                logger.log_info(f"订单响应：{order_response}")

if __name__ == "__main__":
    main()
