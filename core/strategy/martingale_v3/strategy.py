# core/strategy/martingale_v3/strategy.py
from core.strategy.base import StrategyBase, StrategyContext, TradingSignal, SignalType
from core.services.order_service import build_order
from core.services.risk_service import should_pause_due_to_fast_add
from core.logger import logger
from core.domain.enums import PositionField
from typing import Dict, Any, List

class MartingaleV3Strategy(StrategyBase):
    def get_required_params(self) -> List[str]:
        """返回必需的参数列表"""
        return ['symbol', 'base_quantity', 'max_drawdown']
    
    def get_default_params(self) -> Dict[str, Any]:
        """返回默认参数字典"""
        return {
            'symbol': 'ETHUSDT',
            'base_quantity': 1.0,
            'max_drawdown': 0.1,
            'add_ratio': 1.5,
            'take_profit_pct': 0.02
        }
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """验证参数有效性"""
        errors = []
        
        if 'symbol' not in params:
            errors.append("缺少参数: symbol")
        elif not isinstance(params['symbol'], str):
            errors.append("symbol必须是字符串")
            
        if 'base_quantity' not in params:
            errors.append("缺少参数: base_quantity")
        elif not isinstance(params['base_quantity'], (int, float)) or params['base_quantity'] <= 0:
            errors.append("base_quantity必须是正数")
            
        return errors
    
    def initialize(self, context: StrategyContext) -> bool:
        """初始化策略"""
        try:
            # 初始化运行时数据
            self.runtime_data = {
                'last_signal_time': 0,
                'position_size': 0,
                'average_price': 0,
                'add_count': 0
            }
            
            logger.log_info(f"Martingale V3 策略初始化成功: {context.symbol}")
            return True
        except Exception as e:
            logger.log_error(f"Martingale V3 策略初始化失败: {e}")
            return False
    
    def generate_signal(self, context: StrategyContext) -> TradingSignal:
        """生成交易信号"""
        try:
            # 获取当前位置信息
            current_price = context.current_price
            
            # 默认无信号
            signal = TradingSignal(
                signal_type=SignalType.NONE,
                symbol=context.symbol,
                quantity=0,
                reason="暂无交易信号"
            )
            
            # 简单的马丁策略逻辑
            if self.runtime_data.get('position_size', 0) == 0:
                # 没有持仓，开仓
                signal = TradingSignal(
                    signal_type=SignalType.OPEN_LONG,
                    symbol=context.symbol,
                    quantity=self.params.get('base_quantity', 1.0),
                    reason="初始开仓"
                )
            
            return signal
            
        except Exception as e:
            logger.log_error(f"生成交易信号失败: {e}")
            return TradingSignal(
                signal_type=SignalType.NONE,
                symbol=context.symbol,
                quantity=0,
                reason=f"信号生成错误: {e}"
            )

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
