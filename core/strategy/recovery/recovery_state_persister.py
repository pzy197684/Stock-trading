# -*- coding: utf-8 -*-
# core/strategy/recovery/recovery_state_persister.py
# 功能：Recovery策略专用状态持久化管理器 - 处理Recovery策略的复杂状态持久化和恢复
# 注意：此文件与 core/managers/state_manager.py 功能不同
#      - core/managers/state_manager.py: 框架级通用账户状态管理
#      - 本文件: Recovery策略专用的复杂状态持久化管理

from core.logger import logger
from core.state_store import StateStore
from typing import Dict, Any, Optional
import json
import time
from datetime import datetime
from dataclasses import asdict

class RecoveryStatePersister:
    """Recovery策略专用状态持久化管理器
    
    与框架通用StateManager(core/managers/state_manager.py)区别：
    - 通用StateManager: 管理AccountState/PositionState等框架基础状态
    - RecoveryStatePersister: 管理Recovery策略的复杂内部状态持久化
    
    职责：
    - 管理Recovery策略的多层状态结构(long_state, short_state, global_state)
    - 提供配置变更检测和状态兼容性验证
    - 支持状态备份、恢复和迁移功能
    - 处理策略重启后的状态恢复
    """
    
    def __init__(self, strategy_id: str, symbol: str):
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.state_store = StateStore()
        self.state_key = f"recovery_{strategy_id}_{symbol}"
        
    def save_strategy_state(self, strategy_instance) -> bool:
        """保存策略状态到存储"""
        try:
            # 构建状态数据
            state_data = {
                'timestamp': int(time.time()),
                'strategy_id': self.strategy_id,
                'symbol': self.symbol,
                'status': strategy_instance.status.value if hasattr(strategy_instance.status, 'value') else str(strategy_instance.status),
                'long_state': asdict(strategy_instance.long_state),
                'short_state': asdict(strategy_instance.short_state),
                'global_state': {
                    'cap_lock': strategy_instance.cap_lock,
                    'pause_until': strategy_instance.pause_until,
                    'pause_reason': strategy_instance.pause_reason,
                    'boot_reconciled': strategy_instance.boot_reconciled
                },
                'statistics': {
                    'error_count': strategy_instance.error_count,
                    'last_error': strategy_instance.last_error,
                    'trade_count': getattr(strategy_instance, 'trade_count', 0),
                    'last_signal_time': getattr(strategy_instance, 'last_signal_time', 0)
                },
                'config_hash': self._calculate_config_hash(strategy_instance.params)
            }
            
            # 保存到状态存储
            return self.state_store.save_state(self.state_key, state_data)
            
        except Exception as e:
            logger.log_error(f"保存解套策略状态失败: {e}")
            return False
    
    def load_strategy_state(self, strategy_instance) -> bool:
        """从存储加载策略状态"""
        try:
            # 从状态存储加载
            state_data = self.state_store.load_state(self.state_key)
            if not state_data:
                logger.log_info(f"未找到解套策略状态，使用初始状态: {self.state_key}")
                return True
            
            # 验证配置兼容性
            current_config_hash = self._calculate_config_hash(strategy_instance.params)
            saved_config_hash = state_data.get('config_hash', '')
            
            if current_config_hash != saved_config_hash:
                logger.log_warning("配置已变更，重置策略状态")
                return True
            
            # 恢复状态
            self._restore_state(strategy_instance, state_data)
            
            logger.log_info(f"解套策略状态加载成功: {self.state_key}")
            return True
            
        except Exception as e:
            logger.log_error(f"加载解套策略状态失败: {e}")
            return False
    
    def _restore_state(self, strategy_instance, state_data: Dict[str, Any]):
        """恢复策略状态"""
        try:
            # 恢复多头状态
            long_state_data = state_data.get('long_state', {})
            if long_state_data:
                strategy_instance.long_state.qty = float(long_state_data.get('qty', 0))
                strategy_instance.long_state.avg_price = float(long_state_data.get('avg_price', 0))
                strategy_instance.long_state.add_times = int(long_state_data.get('add_times', 0))
                strategy_instance.long_state.last_qty = float(long_state_data.get('last_qty', 0))
                strategy_instance.long_state.last_fill_price = float(long_state_data.get('last_fill_price', 0))
                strategy_instance.long_state.trapped_qty = float(long_state_data.get('trapped_qty', 0))
                strategy_instance.long_state.cap = float(long_state_data.get('cap', 0))
                strategy_instance.long_state.at_full = bool(long_state_data.get('at_full', False))
                strategy_instance.long_state.pending_tp = long_state_data.get('pending_tp', {})
                strategy_instance.long_state.last_trade_id = int(long_state_data.get('last_trade_id', 0))
            
            # 恢复空头状态
            short_state_data = state_data.get('short_state', {})
            if short_state_data:
                strategy_instance.short_state.qty = float(short_state_data.get('qty', 0))
                strategy_instance.short_state.avg_price = float(short_state_data.get('avg_price', 0))
                strategy_instance.short_state.add_times = int(short_state_data.get('add_times', 0))
                strategy_instance.short_state.last_qty = float(short_state_data.get('last_qty', 0))
                strategy_instance.short_state.last_fill_price = float(short_state_data.get('last_fill_price', 0))
                strategy_instance.short_state.trapped_qty = float(short_state_data.get('trapped_qty', 0))
                strategy_instance.short_state.cap = float(short_state_data.get('cap', 0))
                strategy_instance.short_state.at_full = bool(short_state_data.get('at_full', False))
                strategy_instance.short_state.pending_tp = short_state_data.get('pending_tp', {})
                strategy_instance.short_state.last_trade_id = int(short_state_data.get('last_trade_id', 0))
            
            # 恢复全局状态
            global_state = state_data.get('global_state', {})
            strategy_instance.cap_lock = bool(global_state.get('cap_lock', False))
            strategy_instance.pause_until = int(global_state.get('pause_until', 0))
            strategy_instance.pause_reason = str(global_state.get('pause_reason', ''))
            strategy_instance.boot_reconciled = bool(global_state.get('boot_reconciled', False))
            
            # 恢复统计信息
            statistics = state_data.get('statistics', {})
            strategy_instance.error_count = int(statistics.get('error_count', 0))
            strategy_instance.last_error = str(statistics.get('last_error', ''))
            
            if hasattr(strategy_instance, 'trade_count'):
                strategy_instance.trade_count = int(statistics.get('trade_count', 0))
            if hasattr(strategy_instance, 'last_signal_time'):
                strategy_instance.last_signal_time = int(statistics.get('last_signal_time', 0))
            
        except Exception as e:
            logger.log_error(f"恢复策略状态时出错: {e}")
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """计算配置哈希值"""
        try:
            # 简单的配置哈希计算
            config_str = json.dumps(config, sort_keys=True)
            return str(hash(config_str))
        except Exception:
            return ""
    
    def clear_state(self) -> bool:
        """清除策略状态"""
        try:
            result = self.state_store.delete_state(self.state_key)
            logger.log_info(f"解套策略状态已清除: {self.state_key}")
            return result
        except Exception as e:
            logger.log_error(f"清除策略状态失败: {e}")
            return False
    
    def get_state_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        try:
            state_data = self.state_store.load_state(self.state_key)
            if not state_data:
                return {'exists': False}
            
            return {
                'exists': True,
                'timestamp': state_data.get('timestamp'),
                'last_update': datetime.fromtimestamp(state_data.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                'strategy_id': state_data.get('strategy_id'),
                'symbol': state_data.get('symbol'),
                'status': state_data.get('status'),
                'long_position': {
                    'qty': state_data.get('long_state', {}).get('qty', 0),
                    'add_times': state_data.get('long_state', {}).get('add_times', 0),
                    'at_full': state_data.get('long_state', {}).get('at_full', False)
                },
                'short_position': {
                    'qty': state_data.get('short_state', {}).get('qty', 0),
                    'add_times': state_data.get('short_state', {}).get('add_times', 0),
                    'at_full': state_data.get('short_state', {}).get('at_full', False)
                },
                'global_state': state_data.get('global_state', {}),
                'error_count': state_data.get('statistics', {}).get('error_count', 0)
            }
            
        except Exception as e:
            logger.log_error(f"获取状态摘要失败: {e}")
            return {'exists': False, 'error': str(e)}
    
    def backup_state(self, backup_name: Optional[str] = None) -> bool:
        """备份当前状态"""
        try:
            state_data = self.state_store.load_state(self.state_key)
            if not state_data:
                logger.log_warning("没有状态可备份")
                return False
            
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{timestamp}"
            
            backup_key = f"{self.state_key}_{backup_name}"
            result = self.state_store.save_state(backup_key, state_data)
            
            if result:
                logger.log_info(f"状态备份成功: {backup_key}")
            
            return result
            
        except Exception as e:
            logger.log_error(f"备份状态失败: {e}")
            return False
    
    def restore_from_backup(self, backup_name: str) -> bool:
        """从备份恢复状态"""
        try:
            backup_key = f"{self.state_key}_{backup_name}"
            backup_data = self.state_store.load_state(backup_key)
            
            if not backup_data:
                logger.log_error(f"备份不存在: {backup_key}")
                return False
            
            # 恢复状态
            result = self.state_store.save_state(self.state_key, backup_data)
            
            if result:
                logger.log_info(f"从备份恢复状态成功: {backup_key}")
            
            return result
            
        except Exception as e:
            logger.log_error(f"从备份恢复状态失败: {e}")
            return False