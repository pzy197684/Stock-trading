# -*- coding: utf-8 -*-
# core/strategy/martingale_hedge/strategy.py
# 功能：马丁对冲策略实现 - 从928项目移植的完整交易逻辑

from core.strategy.base import StrategyBase, StrategyContext, TradingSignal, SignalType, StrategyStatus
from core.services.order_service import build_order
from core.services.risk_service import should_pause_due_to_fast_add
from core.logger import logger
from core.domain.enums import PositionField
from core.domain.models import OrderReq
from core.utils.decimal_ext import Decimal, ZERO
from decimal import ROUND_DOWN
from core.platform.base import OrderSide, OrderType, OrderStatus
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import time
import copy

@dataclass
class HedgeState:
    """锁仓状态数据结构"""
    hedge_locked: bool = False          # 是否已锁仓
    hedge_stop: bool = False            # 是否停止普通策略
    locked_profit: float = 0.0          # 锁定利润
    hedge_locked_on_full: bool = False  # 是否满仓触发锁仓
    cooldown_until: int = 0             # 冷却时间戳

@dataclass 
class DirectionState:
    """单方向状态数据结构"""
    qty: float = 0.0                    # 持仓数量
    avg_price: float = 0.0              # 均价
    add_times: int = 0                  # 加仓次数
    last_qty: float = 0.0               # 上次加仓数量
    last_entry_price: float = 0.0       # 上次开仓价格
    last_fill_price: float = 0.0        # 上次成交价格
    last_fill_ts: int = 0               # 上次成交时间戳
    last_open_ts: int = 0               # 上次开仓时间戳
    add_history: List[Dict] = None      # 加仓历史
    round: int = 1                      # 轮次
    opposite_qty: float = 0.0           # 对侧持仓量
    fast_add_paused_until: int = 0      # 快速加仓暂停至
    
    # 锁仓相关状态
    hedge_state: HedgeState = None
    
    def __post_init__(self):
        if self.add_history is None:
            self.add_history = []
        if self.hedge_state is None:
            self.hedge_state = HedgeState()

class MartingaleHedgeStrategy(StrategyBase):
    """
    马丁对冲策略
    
    核心逻辑：
    1. 双开起步 - 多空各按 first_qty 开仓
    2. 加仓逻辑 - 相对首仓偏离达到add_interval时加仓
    3. 普通止盈 - 首仓/均价止盈
    4. 对冲锁仓 - 浮亏达到触发条件时进入锁仓模式
    5. 解锁止盈 - 锁仓后盈利侧先释放
    6. 解锁止损 - 亏损侧保护释放
    7. 重开机制 - 无仓位时重新开始
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 方向状态管理
        self.long_state = DirectionState()
        self.short_state = DirectionState()
        
        # 全局状态
        self.exchange_fault_until = 0       # 交易所异常冷静期
        self.backfill_done = {"long": False, "short": False}  # 回填标记
        
        # 精度管理
        self.equal_eps = 0.01  # 对冲平衡容差，将从配置读取
        
    def get_required_params(self) -> List[str]:
        """返回必需的参数列表"""
        return [
            'symbol',
            'long', 'short',  # 方向配置必须存在
            'hedge'           # 对冲配置必须存在
        ]
    
    def get_default_params(self) -> Dict[str, Any]:
        """返回默认参数字典"""
        return {
            'symbol': 'ETHUSDT',
            'order_type': 'MARKET',
            'interval': 5,  # 策略执行间隔（秒）
            
            # 多头配置
            'long': {
                'first_qty': 0.01,
                'add_ratio': 2.0,
                'add_interval': 0.02,
                'max_add_times': 3,
                'tp_first_order': 0.01,
                'tp_before_full': 0.015,
                'tp_after_full': 0.02
            },
            
            # 空头配置  
            'short': {
                'first_qty': 0.01,
                'add_ratio': 2.0,
                'add_interval': 0.02,
                'max_add_times': 3,
                'tp_first_order': 0.01,
                'tp_before_full': 0.015,
                'tp_after_full': 0.02
            },
            
            # 对冲配置
            'hedge': {
                'trigger_loss': 0.05,              # 触发对冲的浮亏比例
                'equal_eps': 0.01,                 # 仓位平衡容差
                'min_wait_seconds': 60,            # 锁仓后冷却时间
                'release_tp_after_full': {         # 解锁止盈阈值
                    'long': 0.02,
                    'short': 0.02
                },
                'release_sl_loss_ratio': {         # 解锁止损比例
                    'long': 1.0,
                    'short': 1.0
                }
            },
            
            # 风控配置
            'risk_control': {
                'tp_slippage': 0.002,             # 止盈滑点
                'max_total_qty': 1.0,             # 最大总仓位
                'cooldown_minutes': 1,            # 风控冷却时间
                'fast_add_window': 300            # 快速加仓检测窗口（秒）
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """验证参数有效性"""
        errors = []
        
        # 基础参数验证
        if 'symbol' not in params or not isinstance(params['symbol'], str):
            errors.append("缺少参数: symbol 或格式错误")
            
        # 方向配置验证
        for direction in ['long', 'short']:
            if direction not in params:
                errors.append(f"缺少方向配置: {direction}")
                continue
                
            dir_config = params[direction]
            required_fields = ['first_qty', 'add_ratio', 'add_interval', 'max_add_times']
            for field in required_fields:
                if field not in dir_config:
                    errors.append(f"缺少{direction}.{field}")
                    
        # 对冲配置验证
        if 'hedge' not in params:
            errors.append("缺少对冲配置: hedge")
        else:
            hedge_config = params['hedge']
            if 'trigger_loss' not in hedge_config:
                errors.append("缺少hedge.trigger_loss")
                
        return errors
    
    def initialize(self, context: StrategyContext) -> bool:
        """初始化策略"""
        try:
            # 从配置加载精度参数
            hedge_config = self.params.get('hedge', {})
            self.equal_eps = float(hedge_config.get('equal_eps', 0.01))
            
            # 初始化状态（这里应该从状态存储加载实际状态）
            self._load_state_from_storage(context)
            
            logger.log_info(f"马丁对冲策略初始化成功: {context.symbol}")
            self.status = StrategyStatus.RUNNING
            return True
            
        except Exception as e:
            logger.log_error(f"马丁对冲策略初始化失败: {e}")
            self.status = StrategyStatus.ERROR
            self.last_error = str(e)
            return False
    
    def generate_signal(self, context: StrategyContext) -> TradingSignal:
        """
        生成交易信号 - 马丁对冲策略核心逻辑
        
        执行顺序：
        1. 交易所异常冷静期检查
        2. 人工全平检测与复位  
        3. 锁仓硬闸门（仅走解锁分支）
        4. 预先锁仓判断
        5. 普通策略逻辑（首仓/加仓/止盈）
        """
        try:
            current_price = context.current_price
            symbol = context.symbol
            
            # 1. 交易所异常冷静期检查
            if self._is_in_exchange_cooldown():
                return self._create_no_signal(symbol, "交易所异常冷静期中")
            
            # 2. 更新状态快照（从context获取最新持仓）
            self._update_state_from_context(context)
            
            # 3. 人工全平检测与复位
            reset_signal = self._check_manual_reset(context)
            if reset_signal:
                return reset_signal
            
            # 4. 处理多空两个方向
            for direction in ['long', 'short']:
                state = self.long_state if direction == 'long' else self.short_state
                opposite_state = self.short_state if direction == 'long' else self.long_state
                direction_config = self.params[direction]
                
                logger.log_info(f"🔍 开始处理方向：{direction}")
                
                # 4.1 锁仓硬闸门：仅走解锁分支
                if state.hedge_state.hedge_stop:
                    logger.log_info(f"⛔ 已锁仓停机（{direction}），仅检查解锁条件")
                    
                    # 优先解锁止盈
                    if self._should_hedge_take_profit(direction, state, current_price):
                        return self._create_hedge_take_profit_signal(symbol, direction, state, current_price)
                    
                    # 再检查解锁止损
                    if self._should_hedge_stop_loss(direction, state, opposite_state, current_price):
                        return self._create_hedge_stop_loss_signal(symbol, direction, state, current_price)
                    
                    continue  # 锁仓状态下不执行其他逻辑
                
                # 4.2 预先锁仓判断
                if self._should_hedge(direction, state, opposite_state, current_price):
                    return self._create_hedge_signal(symbol, direction, state, opposite_state, current_price)
                
                # 4.3 冷却期检查
                if self._is_in_cooldown(state):
                    logger.log_info(f"⏳ {direction} 方向处于冷却期")
                    continue
                
                # 4.4 空仓自动解锁
                if state.qty == 0 and opposite_state.qty == 0:
                    self._auto_unlock_empty_positions()
                
                # 4.5 普通策略逻辑
                
                # 首仓开仓
                if self._should_open_first_order(state):
                    return self._create_open_first_signal(symbol, direction, direction_config)
                
                # 首仓止盈
                if self._should_take_profit_first_order(state, direction_config, current_price, direction):
                    return self._create_take_profit_first_signal(symbol, direction, state, current_price)
                
                # 加仓逻辑
                if self._should_add_position(state, direction_config, current_price, direction):
                    # 风控检查：快速加仓保护
                    if self._should_pause_due_to_fast_add(direction, state):
                        logger.log_info(f"⏸️ {direction} 连续加仓风控冷却中，跳过本轮加仓")
                        continue
                    
                    return self._create_add_position_signal(symbol, direction, state, direction_config, current_price)
                
                # 均价止盈
                if self._should_take_profit(state, direction_config, current_price, direction):
                    return self._create_take_profit_signal(symbol, direction, state, direction_config, current_price)
            
            # 无信号
            return self._create_no_signal(symbol, "暂无交易信号")
            
        except Exception as e:
            logger.log_error(f"生成交易信号失败: {e}")
            self.error_count += 1
            self.last_error = str(e)
            return self._create_no_signal(context.symbol, f"信号生成错误: {e}")

    # ============================================================================
    # 辅助判断方法 - 从928项目移植的核心判断逻辑
    # ============================================================================
    
    def _is_in_exchange_cooldown(self) -> bool:
        """检查是否处于交易所异常冷静期"""
        if self.exchange_fault_until <= 0:
            return False
        
        now_ts = int(time.time())
        if self.exchange_fault_until > 10**12:  # 兼容毫秒时间戳
            self.exchange_fault_until //= 1000
            
        return now_ts < self.exchange_fault_until
    
    def _is_in_cooldown(self, state: DirectionState) -> bool:
        """检查方向是否处于冷却期"""
        now_ts = int(time.time())
        cooldown_until = state.hedge_state.cooldown_until
        
        if cooldown_until > 10**12:  # 兼容毫秒时间戳
            cooldown_until //= 1000
            
        return now_ts < cooldown_until
    
    def _should_open_first_order(self, state: DirectionState) -> bool:
        """判断是否应该开首仓"""
        return state.qty == 0
    
    def _should_take_profit_first_order(self, state: DirectionState, config: Dict, price: float, direction: str) -> bool:
        """
        判断是否满足首仓止盈条件：
        - 当前方向持仓数量 > 0
        - 当前加仓次数 == 0（即为首仓）
        - 当前价格达到独立止盈比例
        """
        if state.qty <= 0 or state.add_times > 0:
            return False
        
        if state.avg_price <= 0:
            return False
            
        tp_ratio = config.get("tp_first_order", 0)
        if direction == "long":
            profit_ratio = (price - state.avg_price) / state.avg_price
        else:
            profit_ratio = (state.avg_price - price) / state.avg_price
        
        # 统一滑点容差
        slippage = self._get_slippage()
        logger.log_info(f"🔎 首仓止盈判断 dir={direction}, 盈利={profit_ratio:.6f}, 目标={tp_ratio:.6f}, 滑点={slippage:.4f}")
        
        return profit_ratio >= tp_ratio * (1 - slippage)
    
    def _should_add_position(self, state: DirectionState, config: Dict, price: float, direction: str) -> bool:
        """
        判断是否满足加仓条件：
        - 当前已持仓
        - 未超过最大加仓次数  
        - 当前价格满足加仓条件
        """
        
        # 限仓保护：检查预计总量是否超限
        if not self._check_position_limit(state, config):
            return False
        
        if state.qty <= 0:
            logger.log_info(f"[调试] ➤ 未持仓，不加仓（{direction}）")
            return False
        
        max_add = config.get("max_add_times", 3)
        if state.add_times >= max_add:
            logger.log_info(f"[调试] ➤ 已加仓 {state.add_times} 次，达到上限 {max_add}（{direction}）")
            return False
        
        # 统一锚点：优先 last_fill_price，其次 avg_price
        baseline = state.last_fill_price or state.avg_price
        if baseline <= 0:
            logger.log_info(f"[调试] ➤ 缺少基准价，无法判断加仓（{direction}）")
            return False
        
        interval = float(config.get("add_interval", 0.02))
        target_price = baseline * (1 - interval) if direction == "long" else baseline * (1 + interval)
        deviation = abs(price - baseline) / baseline
        
        logger.log_info(
            f"[预检·加仓] dir={direction} baseline={baseline:.4f} "
            f"interval={interval:.4f} target={target_price:.4f} "
            f"current={price:.4f} deviation={deviation:.4f}"
        )
        
        return (price <= target_price) if direction == "long" else (price >= target_price)
    
    def _should_take_profit(self, state: DirectionState, config: Dict, price: float, direction: str) -> bool:
        """
        判断当前方向是否满足均价止盈条件（含滑点容差）：
        - 已加仓
        - 浮盈达到设定止盈阈值
        """
        if state.qty <= 0 or state.add_times == 0:
            return False
        
        if state.avg_price <= 0:
            return False
        
        # 计算实际浮盈比例
        if direction == "long":
            profit_ratio = (price - state.avg_price) / state.avg_price
        else:
            profit_ratio = (state.avg_price - price) / state.avg_price
        
        max_times = config.get("max_add_times", 0)
        is_full = state.add_times >= max_times
        tp_ratio = config["tp_after_full"] if is_full else config["tp_before_full"]
        
        # 滑点容差
        slippage = self._get_slippage()
        
        logger.log_info(
            f"[调试] ➤ 均价止盈判断 dir={direction}, add_times={state.add_times}, is_full={is_full}, "
            f"profit={profit_ratio:.6f}, target={tp_ratio:.6f}, slip={slippage:.4f}"
        )
        
        return profit_ratio >= tp_ratio * (1 - slippage)
    
    def _should_hedge(self, direction: str, state: DirectionState, opposite_state: DirectionState, price: float) -> bool:
        """
        判断是否应触发锁仓（反向对冲）：
        1）仅在已满仓时评估
        2）当前方向浮亏比例基于最后一次加仓成交价
        3）尚未锁仓
        4）相反方向持仓 ≤ 当前方向持仓
        """
        if state.qty <= 0 or state.hedge_state.hedge_locked:
            return False
        
        # 仅满仓时才评估锁仓
        direction_config = self.params[direction]
        max_add_times = direction_config.get("max_add_times", 3)
        if state.add_times < max_add_times:
            return False
        
        # 获取触发基准价：last_fill_price -> last_entry_price -> avg_price
        base_price = state.last_fill_price or state.last_entry_price or state.avg_price
        if base_price <= 0:
            return False
        
        # 计算浮亏比例
        if direction == "long":
            loss_ratio = (base_price - price) / base_price
        else:
            loss_ratio = (price - base_price) / base_price
        
        if loss_ratio < 0:
            loss_ratio = 0  # 负值按0处理
        
        # 获取触发阈值
        trigger_loss = self.params.get('hedge', {}).get('trigger_loss', 0.05)
        
        # 检查是否满足触发条件
        trigger_condition = (
            loss_ratio >= trigger_loss and 
            state.qty >= opposite_state.qty
        )
        
        if trigger_condition:
            logger.log_info(
                f"🚨 触发锁仓 | dir={direction} "
                f"add={state.add_times}/{max_add_times} base={base_price:.4f} "
                f"px={price:.4f} loss={loss_ratio:.4%} "
                f"trigger={trigger_loss:.4%} qty={state.qty} opp_qty={opposite_state.qty}"
            )
        
        return trigger_condition
    
    def _should_hedge_take_profit(self, direction: str, state: DirectionState, price: float) -> bool:
        """
        检查当前方向是否处于锁仓状态，并达到浮盈止盈解锁条件
        """
        if not state.hedge_state.hedge_locked or state.qty == 0 or state.avg_price == 0:
            return False
        
        # 计算浮盈比例
        if direction == "long":
            profit_ratio = (price - state.avg_price) / state.avg_price
        else:
            profit_ratio = (state.avg_price - price) / state.avg_price
        
        # 获取解锁止盈比例
        release_tp = self.params.get('hedge', {}).get('release_tp_after_full', {})
        tp_threshold = release_tp.get(direction, 0.02)  # 默认2%
        
        # 滑点容差
        slippage = self._get_slippage()
        eff_target = tp_threshold * (1 - slippage)
        
        logger.log_info(
            f"🔍 解锁止盈判断：方向={direction}, "
            f"当前盈利={profit_ratio:.4f}, 目标={tp_threshold:.4f}, "
            f"滑点={slippage:.4f}, 有效阈值={eff_target:.4f}"
        )
        
        return profit_ratio >= eff_target
    
    def _should_hedge_stop_loss(self, direction: str, state: DirectionState, opposite_state: DirectionState, price: float) -> bool:
        """
        检查当前方向是否满足解锁止损（浮亏金额 ≤ locked_profit × release_sl_loss_ratio）
        """
        if (not state.hedge_state.hedge_locked or 
            state.qty == 0 or 
            state.avg_price == 0 or 
            state.hedge_state.locked_profit == 0):
            return False
        
        # 计算当前方向的浮亏金额
        if direction == "long":
            loss_ratio = (state.avg_price - price) / state.avg_price
        else:
            loss_ratio = (price - state.avg_price) / state.avg_price
        
        loss_amount = state.qty * state.avg_price * loss_ratio
        
        if loss_amount <= 0:
            logger.log_info("🟢 解锁止损：当前已转盈利，允许释放")
            return True
        
        # 获取解锁比例限制
        release_sl = self.params.get('hedge', {}).get('release_sl_loss_ratio', {})
        ratio_limit = release_sl.get(direction, 1.0)
        
        logger.log_info(f"🧮 解锁止损判断 → 方向={direction}, 浮亏金额={loss_amount:.2f}, 限制={state.hedge_state.locked_profit * ratio_limit:.2f}")
        
        return loss_amount <= state.hedge_state.locked_profit * ratio_limit
    
    def _should_pause_due_to_fast_add(self, direction: str, state: DirectionState) -> bool:
        """检查是否应因快速加仓而暂停"""
        now_ts = int(time.time())
        paused_until = state.fast_add_paused_until
        
        if paused_until > 10**12:  # 兼容毫秒时间戳
            paused_until //= 1000
            
        return now_ts < paused_until

    # ============================================================================
    # 信号创建方法
    # ============================================================================
    
    def _create_no_signal(self, symbol: str, reason: str) -> TradingSignal:
        """创建无信号"""
        return TradingSignal(
            signal_type=SignalType.NONE,
            symbol=symbol,
            quantity=0,
            reason=reason
        )
    
    def _create_open_first_signal(self, symbol: str, direction: str, config: Dict) -> TradingSignal:
        """创建首仓开仓信号"""
        qty = config.get("first_qty", 0.01)
        signal_type = SignalType.OPEN_LONG if direction == "long" else SignalType.OPEN_SHORT
        
        return TradingSignal(
            signal_type=signal_type,
            symbol=symbol,
            quantity=qty,
            reason=f"{direction}方向首仓开仓"
        )
    
    def _create_add_position_signal(self, symbol: str, direction: str, state: DirectionState, 
                                   config: Dict, price: float) -> TradingSignal:
        """创建加仓信号"""
        # 计算加仓数量
        first_qty = config.get("first_qty", 0.01)
        add_ratio = config.get("add_ratio", 2.0)
        next_qty = first_qty * (add_ratio ** (state.add_times + 1))
        
        signal_type = SignalType.ADD_LONG if direction == "long" else SignalType.ADD_SHORT
        
        return TradingSignal(
            signal_type=signal_type,
            symbol=symbol,
            quantity=next_qty,
            reason=f"{direction}方向第{state.add_times + 1}次加仓"
        )
    
    def _create_take_profit_first_signal(self, symbol: str, direction: str, 
                                        state: DirectionState, price: float) -> TradingSignal:
        """创建首仓止盈信号"""
        signal_type = SignalType.TAKE_PROFIT
        
        return TradingSignal(
            signal_type=signal_type,
            symbol=symbol,
            quantity=state.qty,
            reason=f"{direction}方向首仓止盈",
            metadata={"direction": direction, "profit_type": "first_order"}
        )
    
    def _create_take_profit_signal(self, symbol: str, direction: str, state: DirectionState,
                                  config: Dict, price: float) -> TradingSignal:
        """创建均价止盈信号"""
        signal_type = SignalType.TAKE_PROFIT
        
        return TradingSignal(
            signal_type=signal_type,
            symbol=symbol,
            quantity=state.qty,
            reason=f"{direction}方向均价止盈",
            metadata={"direction": direction, "profit_type": "average"}
        )
    
    def _create_hedge_signal(self, symbol: str, direction: str, state: DirectionState,
                           opposite_state: DirectionState, price: float) -> TradingSignal:
        """创建对冲锁仓信号"""
        # 计算对冲数量
        diff = state.qty - opposite_state.qty
        hedge_qty = abs(diff)
        
        return TradingSignal(
            signal_type=SignalType.HEDGE,
            symbol=symbol,
            quantity=hedge_qty,
            reason=f"触发对冲锁仓 - {direction}方向",
            metadata={
                "direction": direction,
                "trigger_direction": direction,
                "hedge_side": "short" if direction == "long" else "long",
                "trigger_price": price
            }
        )
    
    def _create_hedge_take_profit_signal(self, symbol: str, direction: str, 
                                       state: DirectionState, price: float) -> TradingSignal:
        """创建解锁止盈信号"""
        return TradingSignal(
            signal_type=SignalType.TAKE_PROFIT,
            symbol=symbol,
            quantity=state.qty,
            reason=f"{direction}方向解锁止盈",
            metadata={"direction": direction, "profit_type": "hedge_unlock"}
        )
    
    def _create_hedge_stop_loss_signal(self, symbol: str, direction: str,
                                     state: DirectionState, price: float) -> TradingSignal:
        """创建解锁止损信号"""
        return TradingSignal(
            signal_type=SignalType.STOP_LOSS,
            symbol=symbol,
            quantity=state.qty,
            reason=f"{direction}方向解锁止损",
            metadata={"direction": direction, "stop_type": "hedge_unlock"}
        )

    # ============================================================================
    # 辅助工具方法  
    # ============================================================================
    
    def _get_slippage(self) -> float:
        """获取统一滑点容差"""
        risk_config = self.params.get("risk_control", {})
        return risk_config.get("tp_slippage", 0.002)
    
    def _check_position_limit(self, state: DirectionState, config: Dict) -> bool:
        """检查仓位限制"""
        try:
            # 获取限仓配置
            max_total_qty = (
                self.params.get("risk_control", {}).get("max_total_qty") or
                config.get("max_total_qty") or
                self.params.get("max_total_qty")
            )
            
            if not max_total_qty:
                return True  # 无限制
            
            # 计算下一次加仓量
            first_qty = config.get("first_qty", 0.01)
            add_ratio = config.get("add_ratio", 2.0)
            next_add_qty = first_qty * (add_ratio ** (state.add_times + 1))
            
            projected_qty = state.qty + next_add_qty
            
            logger.log_info(f"🧮 [限仓-预测] 当前={state.qty:.8f} 下一笔={next_add_qty:.8f} 预测总量={projected_qty:.8f} 上限={max_total_qty:.8f}")
            
            if projected_qty > max_total_qty:
                logger.log_info(f"⛔ [限仓-预测] 超限，跳过本次加仓（projected>{max_total_qty:.8f}）")
                return False
                
            return True
            
        except Exception as e:
            logger.log_warning(f"⚠️ [限仓-预测] 检查异常（已忽略）：{e}")
            return True
    
    def _update_state_from_context(self, context: StrategyContext):
        """从上下文更新状态快照"""
        # 更新多头状态
        long_pos = context.position_long or {}
        self.long_state.qty = float(long_pos.get(PositionField.QUANTITY.value, 0))
        self.long_state.avg_price = float(long_pos.get(PositionField.AVERAGE_PRICE.value, 0))
        self.long_state.opposite_qty = float(context.position_short.get(PositionField.QUANTITY.value, 0) or 0)
        
        # 更新空头状态  
        short_pos = context.position_short or {}
        self.short_state.qty = float(short_pos.get(PositionField.QUANTITY.value, 0))
        self.short_state.avg_price = float(short_pos.get(PositionField.AVERAGE_PRICE.value, 0))
        self.short_state.opposite_qty = float(context.position_long.get(PositionField.QUANTITY.value, 0) or 0)
    
    def _load_state_from_storage(self, context: StrategyContext):
        """从存储加载状态 - 实际应用时需要实现持久化存储"""
        # TODO: 实现从状态存储加载
        # 这里应该从 core.state_store 或类似的状态管理器加载持久化状态
        pass
    
    def _save_state_to_storage(self):
        """保存状态到存储 - 实际应用时需要实现持久化存储"""
        # TODO: 实现状态持久化存储
        pass
    
    def _check_manual_reset(self, context: StrategyContext) -> Optional[TradingSignal]:
        """检查人工全平并复位"""
        now_ts = int(time.time())
        
        for direction in ['long', 'short']:
            state = self.long_state if direction == 'long' else self.short_state
            
            # 检查是否满足人工全平条件
            qty_zero = (state.qty == 0)
            has_history = bool(state.add_history)
            has_counts = (state.add_times > 0)
            has_avg = (state.avg_price > 0)
            has_hedge = (state.hedge_state.hedge_locked or 
                        state.hedge_state.hedge_stop or 
                        state.hedge_state.locked_profit != 0)
            
            # 最近有成交痕迹检查
            recent_window = 600  # 10分钟
            has_recent = ((state.last_fill_ts and now_ts - state.last_fill_ts <= recent_window) or
                         (state.last_open_ts and now_ts - state.last_open_ts <= recent_window))
            
            if qty_zero and ((has_history or has_counts or has_avg or has_hedge) or has_recent):
                logger.log_info(f"🧹 检测到 {direction} 方向人工全平，执行复位")
                
                # 复位状态
                state.qty = 0
                state.avg_price = 0
                state.add_times = 0
                state.add_history = []
                state.last_add_time = None
                state.hedge_state = HedgeState()
                state.last_fill_price = 0
                state.last_fill_ts = 0
                state.last_open_ts = 0
                
                # 设置短暂冷却期
                state.hedge_state.cooldown_until = now_ts + 5
                
                # 保存状态
                self._save_state_to_storage()
                
        return None  # 复位不产生交易信号
    
    def _auto_unlock_empty_positions(self):
        """空仓自动解锁"""
        if (self.long_state.qty == 0 and self.short_state.qty == 0 and
            (self.long_state.hedge_state.hedge_locked or self.short_state.hedge_state.hedge_locked or
             self.long_state.hedge_state.hedge_stop or self.short_state.hedge_state.hedge_stop or
             self.long_state.hedge_state.locked_profit != 0 or self.short_state.hedge_state.locked_profit != 0)):
            
            logger.log_info("🧹 自动解锁：检测到多空均为空仓，清除锁仓状态")
            
            # 清除锁仓状态
            self.long_state.hedge_state = HedgeState()
            self.short_state.hedge_state = HedgeState() 
            
            # 保存状态
            self._save_state_to_storage()

    def build_context(self) -> Dict[str, Any]:
        """构建策略所需的上下文信息"""
        return {
            "long_state": {
                "qty": self.long_state.qty,
                "avg_price": self.long_state.avg_price,
                "add_times": self.long_state.add_times,
                "hedge_locked": self.long_state.hedge_state.hedge_locked,
                "hedge_stop": self.long_state.hedge_state.hedge_stop
            },
            "short_state": {
                "qty": self.short_state.qty,
                "avg_price": self.short_state.avg_price,
                "add_times": self.short_state.add_times,
                "hedge_locked": self.short_state.hedge_state.hedge_locked,
                "hedge_stop": self.short_state.hedge_state.hedge_stop
            },
            "locked": (self.long_state.hedge_state.hedge_locked or 
                      self.short_state.hedge_state.hedge_locked),
            "should_lock": False,    # 由generate_signal动态判断
            "should_unlock": False   # 由generate_signal动态判断
        }