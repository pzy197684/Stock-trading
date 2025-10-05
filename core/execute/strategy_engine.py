# -*- coding: utf-8 -*-
# core/execute/strategy_engine.py
# 功能：策略执行引擎 - 基于现有架构的正确集成

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from core.managers.strategy_manager import get_strategy_manager, StrategyInstance
from core.managers.platform_manager import get_platform_manager
from core.domain.enums import Platform, Direction
from core.strategy.base import StrategyContext, TradingSignal, SignalType, StrategyStatus
from core.logger import logger


class StrategyEngine:
    """策略执行引擎"""
    
    def __init__(self):
        self.strategy_manager = get_strategy_manager()
        self.platform_manager = get_platform_manager()
        self.running = False
        self.execution_tasks = {}  # account -> asyncio.Task
        self.last_execution_times = {}  # instance_id -> timestamp
        
    async def start(self):
        """启动策略执行引擎"""
        if self.running:
            logger.log_warning("策略引擎已在运行中")
            return
            
        self.running = True
        logger.log_info("🚀 策略执行引擎启动")
        
        # 启动监控任务
        asyncio.create_task(self._monitor_strategies())
        
    async def _monitor_strategies(self):
        """监控策略状态和执行"""
        logger.log_info("🔄 开始监控策略状态")
        
        while self.running:
            try:
                instances = self.strategy_manager.list_strategy_instances()
                
                for account, instance_list in instances.items():
                    if instance_list and account not in self.execution_tasks:
                        # 发现新的账户有策略，启动执行任务
                        task = asyncio.create_task(self._execute_account_strategies(account))
                        self.execution_tasks[account] = task
                        logger.log_info(f"🆕 检测到新策略，为账户 {account} 启动执行任务")
                
                # 每5秒检查一次
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.log_error(f"监控策略时发生错误: {e}")
                await asyncio.sleep(5)
        
    async def stop(self):
        """停止策略执擎"""
        if not self.running:
            return
            
        self.running = False
        logger.log_info("⏹️  策略执行引擎停止")
        
        # 停止所有执行任务
        for task in self.execution_tasks.values():
            task.cancel()
        
        # 等待任务完成
        if self.execution_tasks:
            await asyncio.gather(*self.execution_tasks.values(), return_exceptions=True)
        
        self.execution_tasks.clear()
    
    async def _execute_account_strategies(self, account: str):
        """执行指定账户的所有策略"""
        logger.log_info(f"🔄 开始执行账户 {account} 的策略")
        
        while self.running:
            try:
                # 获取账户的所有策略实例
                instances = self.strategy_manager.strategy_instances.get(account, {})
                
                for instance_id, instance in instances.items():
                    if instance.strategy.status == StrategyStatus.RUNNING:
                        await self._execute_strategy_instance(account, instance)
                
                # 休眠1秒后继续下一轮
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                logger.log_info(f"账户 {account} 策略执行任务被取消")
                break
            except Exception as e:
                logger.log_error(f"账户 {account} 策略执行异常: {e}")
                await asyncio.sleep(5.0)  # 出错后等待5秒
    
    async def _execute_strategy_instance(self, account: str, instance: StrategyInstance):
        """执行单个策略实例"""
        try:
            instance_id = instance.instance_id
            strategy = instance.strategy
            
            # 检查是否需要执行（基于执行间隔）
            now = time.time()
            last_exec = self.last_execution_times.get(instance_id, 0)
            
            if now - last_exec < instance.execution_interval:
                return  # 还未到执行时间
            
            # 构造策略上下文
            context = await self._build_strategy_context(account, instance)
            if not context:
                return
            
            # 生成交易信号
            signal = strategy.generate_signal(context)
            self.last_execution_times[instance_id] = now
            
            if signal and signal.signal_type != SignalType.NONE:
                logger.log_info(f"📊 策略信号: {account}/{instance_id} -> {signal.signal_type.value} {signal.symbol} {signal.quantity}")
                
                # 执行交易信号
                await self._execute_trading_signal(account, signal, context)
            
        except Exception as e:
            logger.log_error(f"执行策略实例 {account}/{instance.instance_id} 失败: {e}")
    
    async def _build_strategy_context(self, account: str, instance: StrategyInstance) -> Optional[StrategyContext]:
        """构建策略上下文"""
        try:
            strategy = instance.strategy
            
            # 确保params是字典
            if not isinstance(strategy.params, dict):
                logger.log_error(f"❌ Strategy.params is not a dict, it's {type(strategy.params)}: {strategy.params}")
                return None
            
            symbol = strategy.params.get('symbol')
            
            if not symbol:
                logger.log_warning(f"策略 {instance.instance_id} 缺少交易对配置")
                return None
            
            # 确定平台
            platform_name = self._get_platform_for_account(account)
            if not platform_name:
                logger.log_warning(f"无法确定账户 {account} 的交易平台")
                return None
            
            # 获取或创建平台实例
            platform = None
            try:
                platform = self.platform_manager.get_platform(platform_name, account)
            except ValueError as e:
                # 平台实例不存在，尝试创建
                if "available but no instance" in str(e):
                    logger.log_info(f"平台实例不存在，正在创建: {platform_name} - {account}")
                    try:
                        platform = self.platform_manager.create_platform_for_account(account, platform_name)
                        if not platform:
                            logger.log_error(f"创建平台实例失败: {platform_name}/{account}")
                            return None
                    except Exception as create_error:
                        logger.log_error(f"创建平台实例失败: {platform_name}/{account} - {create_error}")
                        logger.log_error(f"错误详情: {type(create_error).__name__}: {create_error}")
                        import traceback
                        logger.log_error(f"堆栈跟踪: {traceback.format_exc()}")
                        return None
                else:
                    # 其他错误，重新抛出
                    logger.log_error(f"获取平台实例失败: {platform_name}/{account} - {e}")
                    return None
            
            if not platform:
                logger.log_error(f"无法获取或创建平台实例: {platform_name}/{account}")
                return None
            
            # 获取当前价格
            price_result = await asyncio.to_thread(platform.get_market_price, symbol)
            current_price = 0.0
            if price_result and not price_result.get('error'):
                current_price = float(price_result.get('price', 0))
            
            if current_price <= 0:
                logger.log_warning(f"无法获取 {symbol} 的有效价格")
                return None
            
            # 获取持仓信息
            positions = await asyncio.to_thread(platform.get_positions, symbol)
            position_long = {}
            position_short = {}
            
            if positions and isinstance(positions, dict):
                # binance get_positions 返回 {"long": {...}, "short": {...}} 格式
                position_long = positions.get('long', {})
                position_short = positions.get('short', {})
            
            # 获取账户余额
            balance = await asyncio.to_thread(platform.get_balance)
            
            return StrategyContext(
                account=account,
                platform=platform_name,
                symbol=symbol,
                current_price=current_price,
                position_long=position_long,
                position_short=position_short,
                balance=balance or {},
                exchange=platform
            )
            
        except Exception as e:
            logger.log_error(f"构建策略上下文失败 {account}/{instance.instance_id}: {e}")
            return None
    
    async def _execute_trading_signal(self, account: str, signal: TradingSignal, context: StrategyContext):
        """执行交易信号"""
        try:
            logger.log_info(f"🔥 执行交易信号: {signal.signal_type.value} {signal.symbol} 数量={signal.quantity}")
            
            # 获取平台实例
            platform = context.exchange
            if not platform:
                logger.log_error(f"无法获取平台实例进行交易")
                return
            
            # 根据信号类型构建订单
            if signal.signal_type in [SignalType.OPEN_LONG, SignalType.ADD_LONG]:
                side = "BUY"
            elif signal.signal_type in [SignalType.OPEN_SHORT, SignalType.ADD_SHORT]:
                side = "SELL"
            elif signal.signal_type == SignalType.TAKE_PROFIT:
                # 根据metadata确定平仓方向
                direction = signal.metadata.get("direction", "long") if signal.metadata else "long"
                side = "SELL" if direction == "long" else "BUY"
            elif signal.signal_type == SignalType.STOP_LOSS:
                # 根据metadata确定止损方向
                direction = signal.metadata.get("direction", "long") if signal.metadata else "long"
                side = "SELL" if direction == "long" else "BUY"
            else:
                logger.log_warning(f"未支持的信号类型: {signal.signal_type}")
                return
            
            # 构建订单参数 - 使用direction字段匹配place_order方法期望的格式
            order_params = {
                "symbol": signal.symbol,
                "direction": side,  # 使用direction而不是side
                "type": "MARKET",  # 使用市价单
                "quantity": signal.quantity,
            }
            
            logger.log_info(f"📤 准备下单: {order_params}")
            
            # 执行下单 - 重点：这里会捕获真实的交易所错误
            try:
                result = await asyncio.to_thread(platform.place_order, order_params)
                
                if result and result.get('status') == 'FILLED':
                    logger.log_trade(
                        action="EXECUTE",
                        symbol=signal.symbol,
                        side=side,
                        quantity=signal.quantity,
                        price=result.get('price', 0),
                        order_id=result.get('orderId'),
                        account=account,
                        status="SUCCESS"
                    )
                    logger.log_info(f"订单详情: {result}")
                else:
                    logger.log_warning(f"⚠️ 订单状态异常: {result}")
                    
            except Exception as order_error:
                # 这里是关键：捕获并记录交易所的错误反馈
                error_msg = str(order_error).lower()
                
                if any(keyword in error_msg for keyword in ['insufficient', '余额不足', 'balance', 'fund']):
                    logger.log_warning(f"💰 资金不足错误: {account} - {order_error}")
                    logger.log_trade(
                        action="FAILED",
                        symbol=signal.symbol,
                        side=side,
                        quantity=signal.quantity,
                        price=0,
                        account=account,
                        error="INSUFFICIENT_BALANCE"
                    )
                elif 'margin' in error_msg:
                    logger.log_warning(f"🔒 保证金不足: {account} - {order_error}")
                    logger.log_trade(
                        action="FAILED",
                        symbol=signal.symbol,
                        side=side,
                        quantity=signal.quantity,
                        price=0,
                        account=account,
                        error="INSUFFICIENT_MARGIN"
                    )
                else:
                    logger.log_error(f"❌ 下单失败: {account} - {order_error}")
                    logger.log_trade(
                        action="FAILED",
                        symbol=signal.symbol,
                        side=side,
                        quantity=signal.quantity,
                        price=0,
                        account=account,
                        error=str(order_error)
                    )
                
                # 继续执行，不中断策略
                return
            
        except Exception as e:
            logger.log_error(f"执行交易信号失败: {e}")
            logger.log_trade(
                action="ERROR",
                symbol=signal.symbol,
                side="UNKNOWN",
                quantity=0,
                price=0,
                account=account,
                error=str(e)
            )
    
    def _get_platform_for_account(self, account: str) -> Optional[str]:
        """根据账户名确定交易平台"""
        if account.startswith('BN'):
            return 'binance'
        elif account.startswith('CW'):
            return 'coinw'
        elif account.startswith('OKX'):
            return 'okx'
        elif account.startswith('DC') or account.startswith('DEEP'):
            return 'coinw'  # DEEP使用COINW平台
        else:
            return None


# 全局策略执行引擎实例
_strategy_engine = None

def get_strategy_engine() -> StrategyEngine:
    """获取全局策略执行引擎实例"""
    global _strategy_engine
    if _strategy_engine is None:
        _strategy_engine = StrategyEngine()
    return _strategy_engine