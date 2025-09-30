# -*- coding: utf-8 -*-
# core/strategy/recovery/__init__.py
# 功能：解套策略模块初始化

from .strategy import RecoveryStrategy
from .executor import RecoveryExecutor
from .recovery_state_persister import RecoveryStatePersister

__all__ = [
    'RecoveryStrategy',
    'RecoveryExecutor',
    'RecoveryStatePersister'
]

# 策略元信息
STRATEGY_INFO = {
    'name': 'recovery',
    'display_name': '解套策略',
    'version': '1.0.0',
    'description': '针对被套持仓的马丁格尔解套策略，支持分层止盈和熔断保护',
    'author': 'Stock Trading System',
    'strategy_class': RecoveryStrategy,
    'executor_class': RecoveryExecutor,
    'supported_platforms': ['binance', 'okx', 'coinw']
}