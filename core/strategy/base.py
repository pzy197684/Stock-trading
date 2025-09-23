from abc import ABC, abstractmethod
from typing import Dict

class StrategyBase(ABC):
    def __init__(self, config: Dict):
        self.config = config
        self.name = config.get("name", "Unnamed Strategy")
    
    @abstractmethod
    def build_context(self):
        """构建策略所需的上下文（如市场行情、持仓等信息）"""
        pass

    @abstractmethod
    def get_plan(self):
        """生成交易计划（如买卖、加仓、止盈等）"""
        pass

    @abstractmethod
    def decide(self):
        """执行决策：基于当前上下文生成下一步操作"""
        pass
