# core/strategy/martingale_v3/strategy.py
from core.strategy.base import StrategyBase
from core.services.order_service import build_order
from core.services.risk_service import should_pause_due_to_fast_add
from core.logger import logger
from core.domain.enums import PositionField

class MartingaleV3Strategy(StrategyBase):
    def build_context(self):
        """构建策略所需的上下文"""
        return {
            "available_capacity": 100,  # 示例：可用仓位
            "cooldown": 0,              # 示例：冷静期
            "circuit_breaker": False,   # 示例：熔断标志
            "locked": False,            # 是否锁仓
            "should_lock": False,       # 是否需要锁仓
            "should_unlock": False      # 是否需要解锁仓位
        }

    def get_plan(self):
        """生成交易计划"""
        return {
            "symbol": "ETHUSDT",
                PositionField.QTY: 1,
            "price": 5000,
            "side": "buy",
            "order_type": "MARKET",
            "timestamp": 1624973580
        }

    def decide(self):
        """执行决策：生成下一步操作"""
        ctx = self.build_context()
        # 检查风控
        logger.log_error(self.get_plan())
        # 示例风控调用
        # allow, reason = allow_risk(ctx, self.get_plan())
        # if not allow:
        #     logger.log_warning(f"风控阻止交易：{reason}")
        #     return None

        # 如果符合风控条件，则生成并执行订单
        plan = self.get_plan()
        return plan
