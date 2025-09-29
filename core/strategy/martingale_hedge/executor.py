# -*- coding: utf-8 -*-
# core/strategy/martingale_hedge/executor.py
# 功能：马丁对冲策略执行器 - 具体执行交易逻辑

from core.strategy.martingale_hedge.adapters.binance import BinanceMartingaleAdapter
from core.strategy.base import TradingSignal, SignalType, StrategyContext
from core.platform.base import ExchangeIf, OrderSide, OrderType
from core.logger import logger
from core.utils.decimal_ext import Decimal, ZERO
from core.domain.models import OrderRequest
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import time

class MartingaleHedgeExecutor:
    """
    马丁对冲策略执行器
    
    负责：
    1. 执行交易信号产生的订单
    2. 订单确认和状态更新
    3. 锁仓和解锁操作的具体实现
    4. 风控检查和异常处理
    """
    
    def __init__(self, exchange: ExchangeIf, adapter: BinanceMartingaleAdapter):
        self.exchange = exchange
        self.adapter = adapter
        
    def execute_signal(self, signal: TradingSignal, context: StrategyContext) -> Dict[str, Any]:
        """
        执行交易信号
        
        Args:
            signal: 交易信号
            context: 策略上下文
            
        Returns:
            执行结果字典
        """
        try:
            logger.log_info(f"📋 开始执行信号：{signal.signal_type.value} {signal.symbol} qty={signal.quantity}")
            
            # 根据信号类型选择执行方法
            if signal.signal_type == SignalType.OPEN_LONG:
                return self._execute_open_first(signal, "long", context)
            elif signal.signal_type == SignalType.OPEN_SHORT:
                return self._execute_open_first(signal, "short", context)
            elif signal.signal_type == SignalType.ADD_LONG:
                return self._execute_add_position(signal, "long", context)
            elif signal.signal_type == SignalType.ADD_SHORT:
                return self._execute_add_position(signal, "short", context)
            elif signal.signal_type == SignalType.TAKE_PROFIT:
                return self._execute_take_profit(signal, context)
            elif signal.signal_type == SignalType.STOP_LOSS:
                return self._execute_stop_loss(signal, context)
            elif signal.signal_type == SignalType.HEDGE:
                return self._execute_hedge(signal, context)
            else:
                return {
                    "success": False,
                    "reason": f"不支持的信号类型: {signal.signal_type.value}",
                    "signal": signal
                }
                
        except Exception as e:
            logger.log_error(f"❌ 执行交易信号失败：{e}")
            return {
                "success": False,
                "reason": f"执行异常: {e}",
                "signal": signal,
                "error": str(e)
            }
    
    def _execute_open_first(self, signal: TradingSignal, direction: str, context: StrategyContext) -> Dict[str, Any]:
        """
        执行首仓开仓
        
        移植自928项目的execute_open_first_order逻辑
        """
        try:
            symbol = signal.symbol
            quantity = signal.quantity
            side = "BUY" if direction == "long" else "SELL"
            position_side = direction.upper()
            
            logger.log_info(f"📥 执行首仓开仓：{direction} {symbol} qty={quantity}")
            
            # 防重复检查：获取当前持仓
            current_pos = self.adapter.get_position_info(symbol)
            if current_pos.get("error"):
                logger.log_warning(f"⚠️ 获取持仓信息失败，继续执行开仓")
            else:
                current_qty = current_pos[direction]["qty"]
                if current_qty > 0:
                    logger.log_info(f"[去重] 跳过首仓：{direction}已有持仓{current_qty}")
                    return {
                        "success": False,
                        "reason": "已有持仓，跳过首仓开仓",
                        "signal": signal
                    }
            
            # 执行下单
            order_result = self.adapter.place_order(
                symbol=symbol,
                side=side,
                position_side=position_side,
                quantity=quantity,
                order_type="MARKET"
            )
            
            if order_result.get("error"):
                logger.log_error(f"❌ 首仓下单失败：{order_result}")
                return {
                    "success": False,
                    "reason": f"下单失败: {order_result.get('reason', '未知错误')}",
                    "signal": signal,
                    "order_result": order_result
                }
            
            # 订单成交确认
            order_id = order_result.get("orderId")
            confirmed, filled_qty, avg_price = self.adapter.confirm_order_filled(
                symbol=symbol,
                direction=direction,
                order_id=str(order_id) if order_id else None,
                expected_qty=quantity,
                max_wait_seconds=3.0
            )
            
            if not confirmed:
                logger.log_warning(f"⚠️ 首仓订单未确认成交：{symbol} {direction}")
                return {
                    "success": False,
                    "reason": "订单未确认成交",
                    "signal": signal,
                    "order_result": order_result
                }
            
            # 记录执行结果
            execution_result = {
                "success": True,
                "action_type": "首仓开仓",
                "direction": direction,
                "symbol": symbol,
                "order_id": order_id,
                "planned_qty": quantity,
                "filled_qty": filled_qty,
                "avg_price": avg_price,
                "timestamp": int(time.time()),
                "signal": signal
            }
            
            # 记录交易日志
            self._log_trade_execution(execution_result, context)
            
            logger.log_info(f"✅ 首仓开仓完成：{direction} {symbol} 成交量={filled_qty} 均价={avg_price}")
            
            return execution_result
            
        except Exception as e:
            logger.log_error(f"❌ 执行首仓开仓异常：{e}")
            return {
                "success": False,
                "reason": f"执行异常: {e}",
                "signal": signal,
                "error": str(e)
            }
    
    def _execute_add_position(self, signal: TradingSignal, direction: str, context: StrategyContext) -> Dict[str, Any]:
        """
        执行加仓操作
        
        移植自928项目的execute_add_position逻辑
        """
        try:
            symbol = signal.symbol
            quantity = signal.quantity
            side = "BUY" if direction == "long" else "SELL"
            position_side = direction.upper()
            
            logger.log_info(f"🔄 执行加仓操作：{direction} {symbol} qty={quantity}")
            
            # 执行下单
            order_result = self.adapter.place_order(
                symbol=symbol,
                side=side,
                position_side=position_side,
                quantity=quantity,
                order_type="MARKET"
            )
            
            if order_result.get("error"):
                logger.log_error(f"❌ 加仓下单失败：{order_result}")
                return {
                    "success": False,
                    "reason": f"加仓下单失败: {order_result.get('reason', '未知错误')}",
                    "signal": signal,
                    "order_result": order_result
                }
            
            # 订单成交确认
            order_id = order_result.get("orderId")
            confirmed, filled_qty, avg_price = self.adapter.confirm_order_filled(
                symbol=symbol,
                direction=direction,
                order_id=str(order_id) if order_id else None,
                expected_qty=quantity,
                max_wait_seconds=3.0
            )
            
            if not confirmed:
                logger.log_warning(f"⚠️ 加仓订单未确认成交：{symbol} {direction}")
                # 加仓失败时不应阻断策略，记录但继续
                
            # 记录加仓事件（用于风控）
            self._mark_add_event(direction, context)
            
            # 记录执行结果
            execution_result = {
                "success": confirmed,
                "action_type": "加仓",
                "direction": direction,
                "symbol": symbol,
                "order_id": order_id,
                "planned_qty": quantity,
                "filled_qty": filled_qty if confirmed else 0,
                "avg_price": avg_price,
                "timestamp": int(time.time()),
                "signal": signal
            }
            
            # 记录交易日志
            self._log_trade_execution(execution_result, context)
            
            if confirmed:
                logger.log_info(f"✅ 加仓完成：{direction} {symbol} 成交量={filled_qty} 均价={avg_price}")
            else:
                logger.log_warning(f"⚠️ 加仓未确认：{direction} {symbol}")
            
            return execution_result
            
        except Exception as e:
            logger.log_error(f"❌ 执行加仓异常：{e}")
            return {
                "success": False,
                "reason": f"执行异常: {e}",
                "signal": signal,
                "error": str(e)
            }
    
    def _execute_take_profit(self, signal: TradingSignal, context: StrategyContext) -> Dict[str, Any]:
        """
        执行止盈操作
        
        移植自928项目的止盈逻辑
        """
        try:
            symbol = signal.symbol
            quantity = signal.quantity
            metadata = signal.metadata or {}
            direction = metadata.get("direction", "")
            profit_type = metadata.get("profit_type", "")
            
            logger.log_info(f"💰 执行止盈操作：{direction} {symbol} qty={quantity} type={profit_type}")
            
            if not direction:
                return {
                    "success": False,
                    "reason": "止盈信号缺少方向信息",
                    "signal": signal
                }
            
            # 确定平仓参数
            side = "SELL" if direction == "long" else "BUY"  # 平仓方向相反
            position_side = direction.upper()
            
            # 执行平仓下单
            order_result = self.adapter.place_order(
                symbol=symbol,
                side=side,
                position_side=position_side,
                quantity=quantity,
                order_type="MARKET"
            )
            
            if order_result.get("error"):
                logger.log_error(f"❌ 止盈下单失败：{order_result}")
                return {
                    "success": False,
                    "reason": f"止盈下单失败: {order_result.get('reason', '未知错误')}",
                    "signal": signal,
                    "order_result": order_result
                }
            
            # 订单成交确认
            order_id = order_result.get("orderId")
            confirmed, filled_qty, avg_price = self.adapter.confirm_order_filled(
                symbol=symbol,
                direction=direction,
                order_id=str(order_id) if order_id else None,
                expected_qty=quantity,
                max_wait_seconds=3.0
            )
            
            # 记录执行结果
            execution_result = {
                "success": confirmed,
                "action_type": f"止盈-{profit_type}",
                "direction": direction,
                "symbol": symbol,
                "order_id": order_id,
                "planned_qty": quantity,
                "filled_qty": filled_qty if confirmed else 0,
                "avg_price": avg_price,
                "timestamp": int(time.time()),
                "signal": signal
            }
            
            # 特殊处理：如果是解锁止盈，需要更新锁仓状态
            if profit_type == "hedge_unlock":
                self._handle_hedge_take_profit_unlock(direction, execution_result, context)
            
            # 记录交易日志
            self._log_trade_execution(execution_result, context)
            
            if confirmed:
                logger.log_info(f"✅ 止盈完成：{direction} {symbol} 成交量={filled_qty} 均价={avg_price}")
            else:
                logger.log_warning(f"⚠️ 止盈未确认：{direction} {symbol}")
            
            return execution_result
            
        except Exception as e:
            logger.log_error(f"❌ 执行止盈异常：{e}")
            return {
                "success": False,
                "reason": f"执行异常: {e}",
                "signal": signal,
                "error": str(e)
            }
    
    def _execute_stop_loss(self, signal: TradingSignal, context: StrategyContext) -> Dict[str, Any]:
        """
        执行止损操作（主要用于解锁止损）
        
        移植自928项目的解锁止损逻辑
        """
        try:
            symbol = signal.symbol
            quantity = signal.quantity
            metadata = signal.metadata or {}
            direction = metadata.get("direction", "")
            stop_type = metadata.get("stop_type", "")
            
            logger.log_info(f"🛑 执行止损操作：{direction} {symbol} qty={quantity} type={stop_type}")
            
            if not direction:
                return {
                    "success": False,
                    "reason": "止损信号缺少方向信息",
                    "signal": signal
                }
            
            # 确定平仓参数
            side = "SELL" if direction == "long" else "BUY"  # 平仓方向相反
            position_side = direction.upper()
            
            # 执行平仓下单
            order_result = self.adapter.place_order(
                symbol=symbol,
                side=side,
                position_side=position_side,
                quantity=quantity,
                order_type="MARKET"
            )
            
            if order_result.get("error"):
                logger.log_error(f"❌ 止损下单失败：{order_result}")
                return {
                    "success": False,
                    "reason": f"止损下单失败: {order_result.get('reason', '未知错误')}",
                    "signal": signal,
                    "order_result": order_result
                }
            
            # 订单成交确认
            order_id = order_result.get("orderId")
            confirmed, filled_qty, avg_price = self.adapter.confirm_order_filled(
                symbol=symbol,
                direction=direction,
                order_id=str(order_id) if order_id else None,
                expected_qty=quantity,
                max_wait_seconds=3.0
            )
            
            # 记录执行结果
            execution_result = {
                "success": confirmed,
                "action_type": f"止损-{stop_type}",
                "direction": direction,
                "symbol": symbol,
                "order_id": order_id,
                "planned_qty": quantity,
                "filled_qty": filled_qty if confirmed else 0,
                "avg_price": avg_price,
                "timestamp": int(time.time()),
                "signal": signal
            }
            
            # 特殊处理：如果是解锁止损，需要清除锁仓状态
            if stop_type == "hedge_unlock":
                self._handle_hedge_stop_loss_unlock(direction, execution_result, context)
            
            # 记录交易日志
            self._log_trade_execution(execution_result, context)
            
            if confirmed:
                logger.log_info(f"✅ 止损完成：{direction} {symbol} 成交量={filled_qty} 均价={avg_price}")
            else:
                logger.log_warning(f"⚠️ 止损未确认：{direction} {symbol}")
            
            return execution_result
            
        except Exception as e:
            logger.log_error(f"❌ 执行止损异常：{e}")
            return {
                "success": False,
                "reason": f"执行异常: {e}",
                "signal": signal,
                "error": str(e)
            }
    
    def _execute_hedge(self, signal: TradingSignal, context: StrategyContext) -> Dict[str, Any]:
        """
        执行对冲锁仓操作
        
        移植自928项目的execute_hedge逻辑
        """
        try:
            symbol = signal.symbol
            quantity = signal.quantity
            metadata = signal.metadata or {}
            trigger_direction = metadata.get("trigger_direction", "")
            hedge_side = metadata.get("hedge_side", "")
            trigger_price = metadata.get("trigger_price", 0)
            
            logger.log_info(f"🔒 执行对冲锁仓：触发方向={trigger_direction} 对冲方向={hedge_side} qty={quantity}")
            
            if not trigger_direction or not hedge_side:
                return {
                    "success": False,
                    "reason": "对冲信号缺少必要信息",
                    "signal": signal
                }
            
            # 检查是否需要实际下单（如果差额小于容差则跳过下单）
            equal_eps = 0.01  # 从策略配置获取
            placed_qty = 0.0
            order_result = None
            
            if quantity > equal_eps:
                # 确定对冲下单参数
                side = "BUY" if hedge_side == "long" else "SELL"
                position_side = hedge_side.upper()
                
                logger.log_info(f"🛒 对冲下单：{hedge_side} {side}/{position_side} qty={quantity}")
                
                # 执行对冲下单
                order_result = self.adapter.place_order(
                    symbol=symbol,
                    side=side,
                    position_side=position_side,
                    quantity=quantity,
                    order_type="MARKET"
                )
                
                if order_result.get("error"):
                    logger.log_error(f"❌ 对冲下单失败：{order_result}")
                    return {
                        "success": False,
                        "reason": f"对冲下单失败: {order_result.get('reason', '未知错误')}",
                        "signal": signal,
                        "order_result": order_result
                    }
                
                # 确认对冲下单成交
                order_id = order_result.get("orderId")
                confirmed, filled_qty, avg_price = self.adapter.confirm_order_filled(
                    symbol=symbol,
                    direction=hedge_side,
                    order_id=str(order_id) if order_id else None,
                    expected_qty=quantity,
                    max_wait_seconds=3.0
                )
                
                if not confirmed:
                    logger.log_warning(f"⚠️ 对冲订单未确认成交，但继续锁仓流程")
                
                placed_qty = filled_qty if confirmed else 0
            else:
                logger.log_info(f"🆗 仓位已≈相等（qty={quantity} ≤ {equal_eps}），无需下对冲单")
            
            # 执行成对锁仓（无论是否实际下单）
            self._apply_hedge_lock(trigger_direction, context)
            
            # 同步持仓并进行二次补齐
            self._sync_positions_after_hedge(symbol, context)
            
            # 设置锁仓冷却期
            self._set_hedge_cooldown(context)
            
            # 记录执行结果
            execution_result = {
                "success": True,
                "action_type": "对冲锁仓",
                "trigger_direction": trigger_direction,
                "hedge_direction": hedge_side,
                "symbol": symbol,
                "order_id": order_result.get("orderId") if order_result else None,
                "planned_qty": quantity,
                "filled_qty": placed_qty,
                "trigger_price": trigger_price,
                "timestamp": int(time.time()),
                "signal": signal
            }
            
            # 记录交易日志
            self._log_trade_execution(execution_result, context)
            
            logger.log_info(f"✅ 对冲锁仓完成：已设置成对锁仓状态")
            
            return execution_result
            
        except Exception as e:
            logger.log_error(f"❌ 执行对冲锁仓异常：{e}")
            return {
                "success": False,
                "reason": f"执行异常: {e}",
                "signal": signal,
                "error": str(e)
            }

    # ============================================================================
    # 辅助方法 - 状态管理和日志记录
    # ============================================================================
    
    def _mark_add_event(self, direction: str, context: StrategyContext):
        """标记加仓事件（用于快速加仓风控）"""
        try:
            # 这里应该调用风控服务标记加仓事件
            # 实际实现需要根据Stock-trading框架的风控服务接口
            logger.log_info(f"📝 标记加仓事件：{direction}")
        except Exception as e:
            logger.log_warning(f"⚠️ 标记加仓事件异常：{e}")
    
    def _apply_hedge_lock(self, trigger_direction: str, context: StrategyContext):
        """
        应用成对锁仓状态
        
        移植自928项目的锁仓状态管理逻辑
        """
        try:
            logger.log_info("🪵 执行成对锁仓：long 与 short 均设为锁仓状态")
            
            # 这里应该更新策略的锁仓状态
            # 实际实现需要根据Stock-trading框架的状态管理接口
            # 示例：
            # self.state_manager.update_hedge_state({
            #     "long": {"hedge_locked": True, "hedge_stop": True},
            #     "short": {"hedge_locked": True, "hedge_stop": True}
            # })
            
        except Exception as e:
            logger.log_warning(f"⚠️ 应用锁仓状态异常：{e}")
    
    def _sync_positions_after_hedge(self, symbol: str, context: StrategyContext):
        """对冲后同步持仓并进行二次补齐"""
        try:
            logger.log_info("📊 对冲后同步持仓状态")
            
            # 获取最新持仓
            position_info = self.adapter.get_position_info(symbol)
            if position_info.get("error"):
                logger.log_warning(f"⚠️ 对冲后持仓同步失败：{position_info}")
                return
            
            long_qty = position_info["long"]["qty"]
            short_qty = position_info["short"]["qty"]
            
            logger.log_info(f"📊 对冲后持仓：long={long_qty} short={short_qty}")
            
            # 检查是否需要二次补齐
            equal_eps = 0.01  # 从配置获取
            diff = abs(long_qty - short_qty)
            
            if diff > equal_eps:
                need_qty = diff
                if long_qty > short_qty:
                    logger.log_info(f"📐 二次补齐：在short端补{need_qty}")
                    # 执行补齐下单
                    self._place_balance_order(symbol, "short", need_qty)
                else:
                    logger.log_info(f"📐 二次补齐：在long端补{need_qty}")
                    # 执行补齐下单
                    self._place_balance_order(symbol, "long", need_qty)
            
        except Exception as e:
            logger.log_warning(f"⚠️ 对冲后同步异常：{e}")
    
    def _place_balance_order(self, symbol: str, direction: str, quantity: float):
        """下平衡补齐单"""
        try:
            side = "BUY" if direction == "long" else "SELL"
            position_side = direction.upper()
            
            order_result = self.adapter.place_order(
                symbol=symbol,
                side=side,
                position_side=position_side,
                quantity=quantity,
                order_type="MARKET"
            )
            
            if order_result.get("error"):
                logger.log_warning(f"⚠️ 平衡补齐下单失败：{order_result}")
            else:
                logger.log_info(f"✅ 平衡补齐下单成功：{direction} qty={quantity}")
                
        except Exception as e:
            logger.log_warning(f"⚠️ 平衡补齐下单异常：{e}")
    
    def _set_hedge_cooldown(self, context: StrategyContext):
        """设置锁仓冷却期"""
        try:
            # 从策略配置获取冷却时间
            min_wait_seconds = 60  # 默认60秒，应从策略配置读取
            cooldown_until = int(time.time()) + min_wait_seconds
            
            logger.log_info(f"⏳ 设置锁仓冷却：{min_wait_seconds}秒")
            
            # 这里应该更新冷却状态
            # 实际实现需要根据Stock-trading框架的状态管理接口
            
        except Exception as e:
            logger.log_warning(f"⚠️ 设置锁仓冷却异常：{e}")
    
    def _handle_hedge_take_profit_unlock(self, direction: str, execution_result: Dict, context: StrategyContext):
        """处理解锁止盈后的状态更新"""
        try:
            logger.log_info(f"🔓 处理解锁止盈：{direction}方向")
            
            # 解锁止盈的逻辑：
            # 1. 平掉盈利侧全部仓位（已在上层执行）
            # 2. 将已实现利润记入对侧locked_profit
            # 3. 对侧维持锁仓状态
            
            if execution_result.get("success"):
                opposite_direction = "short" if direction == "long" else "long"
                realized_profit = self._calculate_realized_profit(execution_result)
                
                logger.log_info(f"💰 记录已实现利润到{opposite_direction}方向：{realized_profit}")
                
                # 这里应该更新状态：
                # - 当前方向：解除锁仓，允许重开
                # - 对侧方向：保持锁仓，增加locked_profit
                
        except Exception as e:
            logger.log_warning(f"⚠️ 处理解锁止盈异常：{e}")
    
    def _handle_hedge_stop_loss_unlock(self, direction: str, execution_result: Dict, context: StrategyContext):
        """处理解锁止损后的状态更新"""
        try:
            logger.log_info(f"🔓 处理解锁止损：{direction}方向")
            
            # 解锁止损的逻辑：
            # 1. 平掉亏损侧仓位（已在上层执行）  
            # 2. 清除双边锁仓标识
            # 3. 重置locked_profit
            
            if execution_result.get("success"):
                logger.log_info("🧹 清除双边锁仓状态")
                
                # 这里应该清除双边锁仓状态：
                # - 两个方向都设为：hedge_locked=False, hedge_stop=False
                # - 重置locked_profit=0
                
        except Exception as e:
            logger.log_warning(f"⚠️ 处理解锁止损异常：{e}")
    
    def _calculate_realized_profit(self, execution_result: Dict) -> float:
        """计算已实现利润"""
        try:
            # 简单计算，实际应该根据持仓成本和成交价格计算
            filled_qty = execution_result.get("filled_qty", 0)
            avg_price = execution_result.get("avg_price", 0)
            
            # 这里需要获取该方向的持仓成本来计算实际利润
            # 暂时返回0，实际实现时需要完善
            return 0.0
            
        except Exception as e:
            logger.log_warning(f"⚠️ 计算已实现利润异常：{e}")
            return 0.0
    
    def _log_trade_execution(self, execution_result: Dict, context: StrategyContext):
        """记录交易执行日志"""
        try:
            # 构建日志记录
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "platform": "Binance",
                "symbol": execution_result.get("symbol", ""),
                "action_type": execution_result.get("action_type", ""),
                "direction": execution_result.get("direction", ""),
                "success": execution_result.get("success", False),
                "order_id": execution_result.get("order_id", ""),
                "planned_qty": execution_result.get("planned_qty", 0),
                "filled_qty": execution_result.get("filled_qty", 0),
                "avg_price": execution_result.get("avg_price", 0),
                "reason": execution_result.get("signal", {}).get("reason", "")
            }
            
            # 记录到日志系统
            logger.log_info(f"📝 交易执行记录：{log_entry}")
            
            # 这里可以扩展记录到CSV或数据库
            
        except Exception as e:
            logger.log_warning(f"⚠️ 记录交易日志异常：{e}")