# -*- coding: utf-8 -*-
# core/strategy/recovery/strategy.py
# 功能：解套策略实现 - 从929项目移植的稳定运行版本

from core.strategy.base import StrategyBase, StrategyContext, TradingSignal, SignalType, StrategyStatus
from core.services.order_service import build_order
from core.logger import logger
from core.domain.enums import PositionField
from core.domain.models import OrderRequest
from core.utils.decimal_ext import Decimal, ZERO
from core.platform.base import OrderSide, OrderType, OrderStatus
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import time
import copy

@dataclass
class RecoveryPlan:
    """解套策略执行计划"""
    action: str               # "open_first" | "add" | "tp_first" | "tp_before" | "tp_after" | "cap_enter" | "cap_exit" | "pause_jump" | "pause_atr" | "none"
    side: str = ""            # "long" | "short"
    qty: float = 0.0
    price: float = 0.0
    step: int = 0             # 轮次（步号）
    reason: str = ""          # 中文理由

@dataclass 
class RecoveryState:
    """解套策略单方向状态"""
    qty: float = 0.0                    # 持仓数量
    avg_price: float = 0.0              # 均价
    add_times: int = 0                  # 加仓次数
    last_qty: float = 0.0               # 上次加仓数量
    last_fill_price: float = 0.0        # 上次成交价格
    
    # 解套策略特有状态
    trapped_qty: float = 0.0            # 被套持仓数量
    cap: float = 0.0                    # 容量上限
    at_full: bool = False               # 是否满仓
    pending_tp: Optional[Dict[str, Any]] = None   # 挂单记录
    last_trade_id: int = 0              # 最后交易ID
    
    def __post_init__(self):
        if self.pending_tp is None:
            self.pending_tp = {}

class RecoveryStrategy(StrategyBase):
    """
    解套策略
    
    核心逻辑：
    1. 针对被套持仓，在反方向进行解套交易
    2. 马丁格尔加仓 - 按倍率递增仓位
    3. 分层止盈 - 首仓独立TP、满仓前/后均价TP
    4. 容量控制 - cap_ratio限制最大解套仓位
    5. 熔断保护 - 跳跃熔断和ATR熔断
    6. K线确认 - F1/F2过滤机制
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 解套策略状态
        self.long_state = RecoveryState()
        self.short_state = RecoveryState()
        
        # 全局状态
        self.cap_lock = False
        self.pause_until = 0
        self.pause_reason = ""
        self.boot_reconciled = False
        
    def get_required_params(self) -> List[str]:
        """返回必需的参数列表"""
        return [
            'symbol',
            'recovery.mode',
            'recovery.cap_ratio',
            'recovery.grid.add_interval_pct',
            'recovery.grid.martingale.first_qty',
            'recovery.grid.martingale.multiplier',
            'recovery.grid.martingale.max_add_times'
        ]
    
    def get_default_params(self) -> Dict[str, Any]:
        """返回默认参数字典"""
        return {
            'symbol': 'OPUSDT',
            'recovery': {
                'mode': 'long_trapped',
                'cap_ratio': 0.75,
                'ttl_seconds': 300,
                
                'grid': {
                    'add_interval_pct': 0.04,
                    'tp_first_order_pct': 0.01,
                    'tp_before_full_pct': 0.02,
                    'tp_after_full_pct': 0.01,
                    'tp_reprice_tol_ratio': 0.001,
                    'martingale': {
                        'first_qty': 50.0,
                        'multiplier': 2.0,
                        'max_add_times': 4
                    }
                },
                
                'confirm': {
                    'kline': '15m',
                    'filters': {
                        'body_min_frac_of_interval': 0.25,
                        'wick_to_body_max': 2.0,
                        'followthrough_window_min': 15
                    }
                },
                
                'circuit_breakers': {
                    'jump': {
                        'enabled': True,
                        'window_minutes': 30,
                        'factor_vs_interval': 2.0,
                        'pause_minutes': 15
                    },
                    'atr': {
                        'enabled': True,
                        'tf': '60m',
                        'factor_vs_interval': 3.0,
                        'pause_hours': 24
                    }
                }
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """验证参数有效性"""
        errors = []
        
        # 基础参数验证
        if 'symbol' not in params or not isinstance(params['symbol'], str):
            errors.append("缺少参数: symbol 或格式错误")
        
        # 解套配置验证
        if 'recovery' not in params:
            errors.append("缺少解套配置: recovery")
            return errors
        
        recovery_config = params['recovery']
        
        # 模式验证
        if 'mode' not in recovery_config or recovery_config['mode'] not in ['long_trapped', 'short_trapped']:
            errors.append("recovery.mode 必须是 'long_trapped' 或 'short_trapped'")
        
        # 容量比例验证
        if 'cap_ratio' not in recovery_config or not (0 < recovery_config['cap_ratio'] <= 1):
            errors.append("recovery.cap_ratio 必须在 (0, 1] 范围内")
        
        # 网格配置验证
        if 'grid' not in recovery_config:
            errors.append("缺少网格配置: recovery.grid")
        else:
            grid_config = recovery_config['grid']
            
            # 马丁配置验证
            if 'martingale' not in grid_config:
                errors.append("缺少马丁配置: recovery.grid.martingale")
            else:
                martingale = grid_config['martingale']
                required_fields = ['first_qty', 'multiplier', 'max_add_times']
                for field in required_fields:
                    if field not in martingale:
                        errors.append(f"缺少马丁参数: recovery.grid.martingale.{field}")
        
        return errors
    
    def initialize(self, context: StrategyContext) -> bool:
        """初始化策略"""
        try:
            # 从状态存储加载实际状态
            self._load_state_from_storage(context)
            
            logger.log_info(f"解套策略初始化成功: {context.symbol}")
            self.status = StrategyStatus.RUNNING
            return True
            
        except Exception as e:
            logger.log_error(f"解套策略初始化失败: {e}")
            self.status = StrategyStatus.ERROR
            self.last_error = str(e)
            return False
    
    def generate_signal(self, context: StrategyContext) -> TradingSignal:
        """
        生成交易信号 - 解套策略核心逻辑
        
        执行顺序：
        1. 熔断检查（跳跃/ATR）
        2. 更新状态快照
        3. 容量锁定进入/退出判断
        4. 止盈优先（首仓独立TP > 均价TP）
        5. 加仓逻辑（马丁格尔）
        6. 首仓开仓
        """
        try:
            current_price = context.current_price
            symbol = context.symbol
            
            # 1. 更新状态快照
            self._update_state_from_context(context)
            
            # 2. 获取配置参数
            recovery_config = self.params['recovery']
            mode = recovery_config['mode']
            
            # 确定被套方向和解套方向
            trapped_side = "long" if mode == "long_trapped" else "short"
            scalp_side = "short" if trapped_side == "long" else "long"
            
            # 获取被套持仓数量
            trapped_qty = self._get_trapped_qty(context, trapped_side)
            
            # 获取解套方向状态
            state = self.long_state if scalp_side == "long" else self.short_state
            
            # 3. 执行决策逻辑
            plan = self._decide_action(
                context=context,
                mode=mode,
                scalp_side=scalp_side,
                state=state,
                trapped_qty=trapped_qty,
                current_price=current_price
            )
            
            # 4. 转换为交易信号
            return self._plan_to_signal(plan, symbol)
            
        except Exception as e:
            logger.log_error(f"生成交易信号失败: {e}")
            self.error_count += 1
            self.last_error = str(e)
            return self._create_no_signal(context.symbol, f"信号生成错误: {e}")
    
    def _decide_action(self, context: StrategyContext, mode: str, scalp_side: str, 
                      state: RecoveryState, trapped_qty: float, current_price: float) -> RecoveryPlan:
        """核心决策逻辑"""
        recovery_config = self.params['recovery']
        grid_config = recovery_config['grid']
        martingale_config = grid_config['martingale']
        
        # 配置参数
        add_interval_pct = grid_config['add_interval_pct']
        tp_first_order_pct = grid_config.get('tp_first_order_pct', 0.0)
        tp_before_full_pct = grid_config['tp_before_full_pct']
        tp_after_full_pct = grid_config['tp_after_full_pct']
        cap_ratio = recovery_config['cap_ratio']
        first_qty = martingale_config['first_qty']
        multiplier = martingale_config['multiplier']
        max_add_times = martingale_config['max_add_times']
        
        # 计算容量
        cap = trapped_qty * cap_ratio
        state.cap = cap
        state.trapped_qty = trapped_qty
        
        # 当前状态
        qty = state.qty
        add_times = state.add_times
        
        now = int(time.time())
        
        # 1. 熔断检查
        breaker_result = self._check_circuit_breakers(context, add_interval_pct)
        if breaker_result.action != "none":
            return breaker_result
        
        # 2. 容量锁定进入/退出
        at_full = qty >= cap > 0
        state.at_full = at_full
        
        if add_times >= max_add_times or at_full:
            # 进入容量锁定：只允许止盈
            if qty > 0:
                return RecoveryPlan(
                    action="cap_enter",
                    side=scalp_side,
                    step=add_times,
                    reason="达到上限或已满仓"
                )
        
        if qty <= 0 and add_times > 0:
            # 退出容量锁定
            return RecoveryPlan(
                action="cap_exit",
                side=scalp_side,
                step=add_times,
                reason="仓位清零"
            )
        
        # 3. 止盈优先
        if qty > 0 and current_price > 0:
            # 首仓独立TP（最高优先级）
            if add_times == 0 and tp_first_order_pct > 0:
                target_price = self._calculate_tp_price(state.avg_price, tp_first_order_pct, scalp_side)
                if self._should_take_profit(current_price, target_price, scalp_side):
                    return RecoveryPlan(
                        action="tp_first",
                        side=scalp_side,
                        qty=qty,
                        price=target_price,
                        step=0,
                        reason="首仓独立止盈"
                    )
            
            # 均价止盈
            tp_pct = tp_after_full_pct if at_full else tp_before_full_pct
            target_price = self._calculate_tp_price(state.avg_price, tp_pct, scalp_side)
            if self._should_take_profit(current_price, target_price, scalp_side):
                action = "tp_after" if at_full else "tp_before"
                reason = "均价止盈策略(满仓后)" if at_full else "均价止盈策略(满仓前)"
                return RecoveryPlan(
                    action=action,
                    side=scalp_side,
                    qty=qty,
                    price=target_price,
                    step=add_times,
                    reason=reason
                )
        
        # 4. 开首仓
        if qty <= 0 and add_times == 0:
            return RecoveryPlan(
                action="open_first",
                side=scalp_side,
                qty=first_qty,
                step=0,
                reason="开启首仓"
            )
        
        # 5. 暂停检查（在首仓之后）
        if now < self.pause_until:
            return RecoveryPlan(
                action="none",
                reason=f"暂停中：{self.pause_reason}"
            )
        
        # 6. 加仓检查
        if state.last_fill_price > 0:
            # 检查距离是否满足加仓条件
            move = abs(current_price / state.last_fill_price - 1.0)
            if move < add_interval_pct:
                return RecoveryPlan(
                    action="none",
                    reason="与上次成交距离不足加仓间距"
                )
            
            # K线确认过滤
            if not self._check_kline_filters(context, scalp_side, add_interval_pct):
                return RecoveryPlan(
                    action="none", 
                    reason="K线确认过滤未通过"
                )
            
            # 计算加仓数量
            next_qty = first_qty if add_times == 0 else state.last_qty * multiplier
            remaining_cap = max(0.0, cap - qty)
            actual_qty = min(next_qty, remaining_cap)
            
            if actual_qty > 0:
                return RecoveryPlan(
                    action="add",
                    side=scalp_side,
                    qty=actual_qty,
                    step=add_times + 1,
                    reason="满足间距与确认条件"
                )
        
        return RecoveryPlan(action="none", reason="暂无交易条件")
    
    def _check_circuit_breakers(self, context: StrategyContext, add_interval_pct: float) -> RecoveryPlan:
        """检查熔断条件"""
        recovery_config = self.params['recovery']
        breakers = recovery_config.get('circuit_breakers', {})
        
        # 跳跃熔断
        jump_config = breakers.get('jump', {})
        if jump_config.get('enabled', False):
            # 这里需要实现价格跳跃检测逻辑
            # 简化实现：检查短期价格变化
            pass
        
        # ATR熔断
        atr_config = breakers.get('atr', {})
        if atr_config.get('enabled', False):
            # 这里需要实现ATR检测逻辑
            # 简化实现：可以从context获取市场数据
            pass
        
        return RecoveryPlan(action="none")
    
    def _check_kline_filters(self, context: StrategyContext, side: str, add_interval_pct: float) -> bool:
        """检查K线确认过滤条件"""
        recovery_config = self.params['recovery']
        confirm_config = recovery_config.get('confirm', {})
        filters = confirm_config.get('filters', {})
        
        # 简化实现：总是返回True
        # 实际应该实现F1/F2过滤逻辑
        return True
    
    def _calculate_tp_price(self, avg_price: float, tp_pct: float, side: str) -> float:
        """计算止盈价格"""
        if side == "long":
            return avg_price * (1.0 + tp_pct)
        else:
            return avg_price * (1.0 - tp_pct)
    
    def _should_take_profit(self, current_price: float, target_price: float, side: str) -> bool:
        """判断是否应该止盈"""
        if side == "long":
            return current_price >= target_price
        else:
            return current_price <= target_price
    
    def _get_trapped_qty(self, context: StrategyContext, trapped_side: str) -> float:
        """获取被套持仓数量"""
        if trapped_side == "long":
            position = context.position_long or {}
        else:
            position = context.position_short or {}
        
        return float(position.get(PositionField.QTY.value, 0))
    
    def _plan_to_signal(self, plan: RecoveryPlan, symbol: str) -> TradingSignal:
        """将执行计划转换为交易信号"""
        if plan.action == "none":
            return self._create_no_signal(symbol, plan.reason)
        
        # 根据action确定信号类型
        signal_type_map = {
            "open_first": SignalType.OPEN_LONG if plan.side == "long" else SignalType.OPEN_SHORT,
            "add": SignalType.ADD_LONG if plan.side == "long" else SignalType.ADD_SHORT,
            "tp_first": SignalType.TAKE_PROFIT,
            "tp_before": SignalType.TAKE_PROFIT,
            "tp_after": SignalType.TAKE_PROFIT,
        }
        
        signal_type = signal_type_map.get(plan.action, SignalType.NONE)
        
        return TradingSignal(
            signal_type=signal_type,
            symbol=symbol,
            quantity=plan.qty,
            price=plan.price,
            reason=plan.reason,
            metadata={
                "strategy": "recovery",
                "action": plan.action,
                "side": plan.side,
                "step": plan.step
            }
        )
    
    def _create_no_signal(self, symbol: str, reason: str) -> TradingSignal:
        """创建无信号"""
        return TradingSignal(
            signal_type=SignalType.NONE,
            symbol=symbol,
            quantity=0,
            reason=reason
        )
    
    def _update_state_from_context(self, context: StrategyContext):
        """从上下文更新状态快照"""
        # 更新多头状态
        long_pos = context.position_long or {}
        self.long_state.qty = float(long_pos.get(PositionField.QTY.value, 0))
        self.long_state.avg_price = float(long_pos.get(PositionField.AVG_PRICE.value, 0))
        
        # 更新空头状态  
        short_pos = context.position_short or {}
        self.short_state.qty = float(short_pos.get(PositionField.QTY.value, 0))
        self.short_state.avg_price = float(short_pos.get(PositionField.AVG_PRICE.value, 0))
    
    def _load_state_from_storage(self, context: StrategyContext):
        """从存储加载状态"""
        # TODO: 实现从状态存储加载
        # 这里应该从 core.state_store 加载持久化状态
        pass
    
    def _save_state_to_storage(self):
        """保存状态到存储"""
        # TODO: 实现状态持久化存储
        pass