# -*- coding: utf-8 -*-
# core/strategy/recovery/adapters/__init__.py
# 功能：解套策略适配器模块初始化

from .binance import RecoveryBinanceAdapter

__all__ = [
    'RecoveryBinanceAdapter'
]

# 适配器注册表
ADAPTER_REGISTRY = {
    'binance': RecoveryBinanceAdapter,
    # 可以在这里添加其他交易所的适配器
    # 'okx': RecoveryOkxAdapter,
    # 'coinw': RecoveryCoinwAdapter,
}