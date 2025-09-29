# -*- coding: utf-8 -*-
# core/strategy/martingale_hedge/adapters/__init__.py
# 功能：马丁对冲策略适配器模块初始化

"""
马丁对冲策略交易所适配器模块

这个模块包含了针对不同交易所的适配器实现：

1. Binance适配器 (binance.py)
   - Binance期货API集成
   - 订单下达和成交确认
   - 持仓查询和余额管理
   - 错误处理和重试机制

适配器设计原则：
- 统一的接口规范，便于扩展其他交易所
- 完善的错误处理和异常恢复
- 详细的日志记录便于调试
- 支持订单确认和持仓同步

支持的交易所：
- Binance期货 (binance.py)
- 其他交易所适配器可以根据需要添加

使用示例：
```python
from core.strategy.martingale_hedge.adapters.binance import BinanceMartingaleAdapter
from core.platform.binance import BinanceExchange

# 创建交易所实例
exchange = BinanceExchange(api_key, api_secret)

# 创建适配器
adapter = BinanceMartingaleAdapter(exchange)

# 使用适配器下单
result = adapter.place_order("ETHUSDT", "BUY", "LONG", 0.01)
```
"""

from .binance import BinanceMartingaleAdapter

__all__ = [
    "BinanceMartingaleAdapter"
]