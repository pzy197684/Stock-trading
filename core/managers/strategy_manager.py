from core.logger import logger
from core.strategy.base import StrategyBase
from typing import List

class StrategyManager:
    def __init__(self, strategies_config: List[dict]):
        self.strategies = []
        for strategy_config in strategies_config:
            strategy_class = self._load_strategy(strategy_config['strategy_name'])
            strategy_instance = strategy_class(strategy_config)
            self.strategies.append(strategy_instance)

    def _load_strategy(self, strategy_name: str):
        """根据策略名称加载对应的策略类"""
        strategy_classes = {
            "martingale_v3": "core.strategy.martingale_v3.strategy.MartingaleV3Strategy",
            # 可以继续添加其他策略
        }
        module_name, class_name = strategy_classes.get(strategy_name, "").rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        strategy_class = getattr(module, class_name)
        return strategy_class

    def get_active_strategies(self):
        """获取所有活跃的策略实例"""
        return self.strategies
