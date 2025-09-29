# -*- coding: utf-8 -*-
# core/strategy/martingale_hedge/__init__.py
# 功能：马丁对冲策略模块初始化

"""
马丁对冲策略模块

这个模块包含了从928项目移植的完整马丁对冲策略实现，包括：

1. 策略核心逻辑 (strategy.py)
   - 双开起步（多空各按first_qty开仓）
   - 动态加仓（偏离达到add_interval时按add_ratio加仓）
   - 分级止盈（首仓止盈/均价止盈）
   - 对冲锁仓（浮亏达到trigger_loss时触发锁仓）
   - 解锁机制（解锁止盈/解锁止损）
   - 重开机制（无仓位时重新开始）

2. 交易所适配器 (adapters/)
   - Binance期货API适配器
   - 订单下达和成交确认
   - 持仓查询和状态同步

3. 策略执行器 (executor.py)
   - 具体交易信号的执行逻辑
   - 锁仓和解锁操作的实现
   - 风控检查和异常处理

关键特性：
- 完整移植928项目的实盘验证交易逻辑
- 适配Stock-trading框架的分层架构
- 支持Binance期货交易
- 包含完善的风控和异常处理机制
- 保持与原有框架的兼容性

使用示例：
```python
from core.strategy.martingale_hedge import MartingaleHedgeStrategy

# 创建策略实例
config = {
    "name": "martingale_hedge_ethusdt",
    "params": {
        "symbol": "ETHUSDT",
        "long": {"first_qty": 0.01, ...},
        "short": {"first_qty": 0.01, ...},
        "hedge": {"trigger_loss": 0.05, ...}
    }
}
strategy = MartingaleHedgeStrategy(config)
```

注意事项：
- 马丁策略存在连续亏损风险，需要充足资金
- 对冲锁仓会占用较多保证金
- 建议在波动较大的市场中使用
- 请合理设置仓位大小和风控参数
"""

from .strategy import MartingaleHedgeStrategy
from .executor import MartingaleHedgeExecutor

# 版本信息
__version__ = "1.0.0"
__author__ = "从928项目移植"
__description__ = "马丁对冲策略 - 完整的双向对冲交易策略实现"

# 导出主要类
__all__ = [
    "MartingaleHedgeStrategy",
    "MartingaleHedgeExecutor"
]

# 策略元信息
STRATEGY_INFO = {
    "name": "马丁对冲策略",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "supported_platforms": ["binance"],
    "strategy_type": "grid_hedge",
    "risk_level": "high",
    "complexity": "advanced"
}