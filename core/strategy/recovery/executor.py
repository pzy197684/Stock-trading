# -*- coding: utf-8 -*-
# core/strategy/recovery/executor.py
# 功能：解套策略执行器 - 处理订单执行和状态更新

from core.execute.strategy_executor import StrategyExecutor
from core.logger import logger
from core.domain.enums import OrderStatus, OrderSide, OrderType
from core.domain.models import OrderRequest, Order
from core.utils.decimal_ext import Decimal, ZERO
from typing import Dict, Any, List, Optional
import time

class RecoveryExecutor(StrategyExecutor):
    """解套策略执行器"""
    
    def __init__(self, strategy_config: Dict[str, Any]):
        super().__init__(strategy_config)
        self.strategy_name = "recovery"
        
        # 解套执行器状态
        self.pending_orders: Dict[str, Order] = {}  # 挂单记录
        self.last_trade_id = 0                      # 最后交易ID
        self.execution_stats = {
            "total_trades": 0,
            "successful_tp": 0,
            "failed_orders": 0,
            "avg_execution_time": 0.0
        }
    
    def execute_signal(self, signal, context) -> bool:
        """
        执行交易信号
        
        解套策略信号类型：
        - open_first: 开启首仓
        - add: 马丁加仓
        - tp_first: 首仓独立止盈
        - tp_before: 满仓前均价止盈
        - tp_after: 满仓后均价止盈
        """
        try:
            start_time = time.time()
            signal_type = signal.signal_type.value
            action = signal.metadata.get('action', '')
            
            logger.log_info(f"执行解套信号: {action} | {signal_type} | {signal.symbol}")
            
            # 根据不同action执行对应逻辑
            if action in ["open_first", "add"]:
                result = self._execute_market_order(signal, context)
            elif action in ["tp_first", "tp_before", "tp_after"]:
                result = self._execute_take_profit(signal, context)
            else:
                logger.log_warning(f"未知的解套策略action: {action}")
                return False
            
            # 更新执行统计
            execution_time = time.time() - start_time
            self._update_execution_stats(result, execution_time)
            
            return result
            
        except Exception as e:
            logger.log_error(f"执行解套信号失败: {e}")
            self.execution_stats["failed_orders"] += 1
            return False
    
    def _execute_market_order(self, signal, context) -> bool:
        """执行市价开仓/加仓订单"""
        try:
            symbol = signal.symbol
            quantity = signal.quantity
            side = signal.metadata.get('side')
            action = signal.metadata.get('action')
            step = signal.metadata.get('step', 0)
            
            # 构建订单请求
            order_side = OrderSide.BUY if side == "long" else OrderSide.SELL
            
            order_request = OrderRequest(
                symbol=symbol,
                side=order_side,
                order_type=OrderType.MARKET,
                quantity=Decimal(str(quantity)),
                metadata={
                    "strategy": self.strategy_name,
                    "action": action,
                    "step": step,
                    "reason": signal.reason
                }
            )
            
            # 提交订单
            order = self.order_service.place_order(order_request)
            if not order:
                logger.log_error(f"订单提交失败: {order_request}")
                return False
            
            # 记录挂单
            self.pending_orders[order.client_order_id] = order
            
            logger.log_info(f"解套{action}订单已提交: {order.client_order_id} | {side} {quantity} @ Market")
            return True
            
        except Exception as e:
            logger.log_error(f"执行市价订单失败: {e}")
            return False
    
    def _execute_take_profit(self, signal, context) -> bool:
        """执行止盈订单"""
        try:
            symbol = signal.symbol
            quantity = signal.quantity
            price = signal.price
            side = signal.metadata.get('side')
            action = signal.metadata.get('action')
            step = signal.metadata.get('step', 0)
            
            # 止盈订单方向与持仓相反
            order_side = OrderSide.SELL if side == "long" else OrderSide.BUY
            
            # 根据策略配置决定订单类型（限价或市价）
            recovery_config = self.strategy_config.get('recovery', {})
            use_limit_tp = recovery_config.get('use_limit_tp', True)
            
            if use_limit_tp and price > 0:
                # 限价止盈
                order_type = OrderType.LIMIT
                order_price = Decimal(str(price))
            else:
                # 市价止盈
                order_type = OrderType.MARKET
                order_price = None
            
            order_request = OrderRequest(
                symbol=symbol,
                side=order_side,
                order_type=order_type,
                quantity=Decimal(str(quantity)),
                price=order_price,
                metadata={
                    "strategy": self.strategy_name,
                    "action": action,
                    "step": step,
                    "reason": signal.reason,
                    "tp_type": action
                }
            )
            
            # 提交订单
            order = self.order_service.place_order(order_request)
            if not order:
                logger.log_error(f"止盈订单提交失败: {order_request}")
                return False
            
            # 记录挂单
            self.pending_orders[order.client_order_id] = order
            
            price_str = f"@ {price}" if price > 0 else "@ Market"
            logger.log_info(f"解套止盈订单已提交: {order.client_order_id} | {action} {quantity} {price_str}")
            return True
            
        except Exception as e:
            logger.log_error(f"执行止盈订单失败: {e}")
            return False
    
    def handle_order_update(self, order: Order) -> bool:
        """处理订单状态更新"""
        try:
            client_order_id = order.client_order_id
            
            # 检查是否是我们的订单
            if client_order_id not in self.pending_orders:
                return True
            
            pending_order = self.pending_orders[client_order_id]
            action = pending_order.metadata.get('action', '')
            
            logger.log_info(f"解套订单状态更新: {client_order_id} | {order.status.value} | {action}")
            
            if order.status == OrderStatus.FILLED:
                # 订单完全成交
                self._handle_order_filled(order)
                del self.pending_orders[client_order_id]
                
            elif order.status == OrderStatus.PARTIALLY_FILLED:
                # 部分成交，更新记录
                self.pending_orders[client_order_id] = order
                
            elif order.status in [OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.FAILED]:
                # 订单失败
                self._handle_order_failed(order)
                del self.pending_orders[client_order_id]
                
            return True
            
        except Exception as e:
            logger.log_error(f"处理订单更新失败: {e}")
            return False
    
    def _handle_order_filled(self, order: Order):
        """处理订单成交"""
        try:
            action = order.metadata.get('action', '')
            step = order.metadata.get('step', 0)
            filled_qty = float(order.filled_quantity)
            avg_price = float(order.average_price) if order.average_price else 0.0
            
            logger.log_info(f"解套订单成交: {action} | 数量={filled_qty} | 均价={avg_price}")
            
            # 更新策略状态
            self._update_strategy_state(order)
            
            # 更新统计
            self.execution_stats["total_trades"] += 1
            if action.startswith("tp_"):
                self.execution_stats["successful_tp"] += 1
            
            # 记录最后交易ID
            if hasattr(order, 'trade_id') and order.trade_id:
                self.last_trade_id = max(self.last_trade_id, order.trade_id)
            
        except Exception as e:
            logger.log_error(f"处理订单成交失败: {e}")
    
    def _handle_order_failed(self, order: Order):
        """处理订单失败"""
        try:
            action = order.metadata.get('action', '')
            reason = order.metadata.get('reason', '')
            
            logger.log_warning(f"解套订单失败: {action} | 状态={order.status.value} | 原因={reason}")
            
            # 更新失败统计
            self.execution_stats["failed_orders"] += 1
            
            # TODO: 根据失败类型决定是否重试
            # 对于重要的止盈订单，可能需要重试机制
            
        except Exception as e:
            logger.log_error(f"处理订单失败时出错: {e}")
    
    def _update_strategy_state(self, order: Order):
        """更新策略状态"""
        try:
            action = order.metadata.get('action', '')
            side = order.side.value.lower()
            filled_qty = float(order.filled_quantity)
            avg_price = float(order.average_price) if order.average_price else 0.0
            
            # 获取策略实例
            strategy = self.get_strategy_instance()
            if not strategy:
                return
            
            # 更新对应方向的状态
            if side in ["buy", "long"]:
                state = strategy.long_state
            else:
                state = strategy.short_state
            
            if action in ["open_first", "add"]:
                # 开仓/加仓：更新持仓数量、均价、加仓次数
                old_qty = state.qty
                old_avg = state.avg_price
                
                # 更新均价
                if old_qty > 0 and old_avg > 0:
                    total_cost = old_qty * old_avg + filled_qty * avg_price
                    new_qty = old_qty + filled_qty
                    new_avg = total_cost / new_qty if new_qty > 0 else 0.0
                else:
                    new_qty = filled_qty
                    new_avg = avg_price
                
                state.qty = new_qty
                state.avg_price = new_avg
                state.last_qty = filled_qty
                state.last_fill_price = avg_price
                
                if action == "add":
                    state.add_times += 1
                
                logger.log_info(f"更新{side}状态: 数量={new_qty} | 均价={new_avg} | 加仓次数={state.add_times}")
                
            elif action.startswith("tp_"):
                # 止盈：减少持仓数量
                state.qty = max(0.0, state.qty - filled_qty)
                
                # 如果仓位清零，重置状态
                if state.qty <= 0:
                    state.qty = 0.0
                    state.avg_price = 0.0
                    state.add_times = 0
                    state.last_qty = 0.0
                    state.at_full = False
                
                logger.log_info(f"执行{action}止盈: 剩余数量={state.qty}")
            
            # 保存状态到存储
            strategy._save_state_to_storage()
            
        except Exception as e:
            logger.log_error(f"更新策略状态失败: {e}")
    
    def _update_execution_stats(self, success: bool, execution_time: float):
        """更新执行统计"""
        try:
            if success:
                # 更新平均执行时间
                total_count = self.execution_stats["total_trades"] + 1
                current_avg = self.execution_stats["avg_execution_time"]
                new_avg = (current_avg * (total_count - 1) + execution_time) / total_count
                self.execution_stats["avg_execution_time"] = new_avg
            
        except Exception as e:
            logger.log_error(f"更新执行统计失败: {e}")
    
    def get_strategy_instance(self):
        """获取策略实例（需要由策略管理器提供）"""
        # TODO: 这里需要实现获取策略实例的逻辑
        # 可能需要通过策略管理器或注册机制获取
        return None
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        pending_count = len(self.pending_orders)
        
        return {
            "strategy": self.strategy_name,
            "pending_orders": pending_count,
            "total_trades": self.execution_stats["total_trades"],
            "successful_tp": self.execution_stats["successful_tp"],
            "failed_orders": self.execution_stats["failed_orders"],
            "avg_execution_time": round(self.execution_stats["avg_execution_time"], 3),
            "last_trade_id": self.last_trade_id
        }
    
    def cleanup_expired_orders(self, ttl_seconds: int = 300):
        """清理过期订单"""
        try:
            current_time = time.time()
            expired_orders = []
            
            for client_order_id, order in self.pending_orders.items():
                # 检查订单是否超时
                order_age = current_time - (order.create_time / 1000 if order.create_time else current_time)
                if order_age > ttl_seconds:
                    expired_orders.append(client_order_id)
            
            # 取消过期订单
            for client_order_id in expired_orders:
                order = self.pending_orders[client_order_id]
                logger.log_warning(f"取消过期订单: {client_order_id} | 年龄={order_age:.1f}秒")
                
                # 调用订单服务取消订单
                cancel_result = self.order_service.cancel_order(order.symbol, client_order_id)
                if cancel_result:
                    del self.pending_orders[client_order_id]
            
        except Exception as e:
            logger.log_error(f"清理过期订单失败: {e}")
    
    def reset_statistics(self):
        """重置执行统计"""
        self.execution_stats = {
            "total_trades": 0,
            "successful_tp": 0,
            "failed_orders": 0,
            "avg_execution_time": 0.0
        }
        logger.log_info("解套策略执行统计已重置")