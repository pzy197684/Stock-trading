# -*- coding: utf-8 -*-
# core/strategy/recovery/adapters/binance.py
# 功能：解套策略的Binance适配器 - 处理Binance特定的API调用和数据格式

from core.platform.binance import BinancePlatform
from core.logger import logger
from core.utils.decimal_ext import Decimal, ZERO
from typing import Dict, Any, List, Optional, Tuple
import time
from datetime import datetime, timedelta

class RecoveryBinanceAdapter:
    """解套策略Binance平台适配器"""
    
    def __init__(self, platform: BinancePlatform, config: Dict[str, Any]):
        self.platform = platform
        self.config = config
        self.symbol = config.get('symbol', 'OPUSDT')
        
        # 缓存相关
        self.price_cache = {}
        self.cache_ttl = 5  # 5秒缓存
        
    def get_current_price(self) -> float:
        """获取当前价格（带缓存）"""
        try:
            now = time.time()
            cache_key = f"price_{self.symbol}"
            
            # 检查缓存
            if cache_key in self.price_cache:
                cached_price, cached_time = self.price_cache[cache_key]
                if now - cached_time < self.cache_ttl:
                    return cached_price
            
            # 获取最新价格
            price_result = self.platform.get_market_price(self.symbol)
            if price_result and not price_result.get('error') and 'price' in price_result:
                price = float(price_result['price'])
                self.price_cache[cache_key] = (price, now)
                return price
            
            logger.log_warning(f"无法获取{self.symbol}价格")
            return 0.0
            
        except Exception as e:
            logger.log_error(f"获取当前价格失败: {e}")
            return 0.0
    
    def get_position_info(self, side: str) -> Dict[str, Any]:
        """获取持仓信息"""
        try:
            positions = self.platform.get_positions(self.symbol)
            if not positions:
                return {}
            
            # 查找对应方向的持仓
            for pos in positions:
                pos_side = pos.get('side', '').lower()
                if pos_side == side.lower():
                    return {
                        'quantity': float(pos.get('quantity', 0)),
                        'avg_price': float(pos.get('average_price', 0)),
                        'unrealized_pnl': float(pos.get('unrealized_pnl', 0)),
                        'percentage': float(pos.get('percentage', 0))
                    }
            
            return {}
            
        except Exception as e:
            logger.log_error(f"获取持仓信息失败: {e}")
            return {}
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额信息"""
        try:
            balance = self.platform.get_balance()
            if not balance:
                return {}
            
            return {
                'total_balance': float(balance.get('total_balance', 0)),
                'available_balance': float(balance.get('available_balance', 0)),
                'used_balance': float(balance.get('used_balance', 0)),
                'unrealized_pnl': float(balance.get('unrealized_pnl', 0))
            }
            
        except Exception as e:
            logger.log_error(f"获取账户余额失败: {e}")
            return {}
    
    def get_kline_data(self, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        用于解套策略的确认过滤功能：
        - F1: 实体占比过滤
        - F2: 影线比例过滤
        - F3: 跟进确认窗口
        """
        try:
            # 转换timeframe格式
            interval = self._convert_timeframe(timeframe)
            
            # 获取K线数据
            klines = self.platform.get_klines(
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            
            if not klines:
                return []
            
            # 转换为标准格式
            formatted_klines = []
            for kline in klines:
                formatted_klines.append({
                    'timestamp': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': int(kline[6])
                })
            
            return formatted_klines
            
        except Exception as e:
            logger.log_error(f"获取K线数据失败: {e}")
            return []
    
    def calculate_atr(self, timeframe: str = '1h', period: int = 14) -> float:
        """
        计算ATR (Average True Range)
        
        用于解套策略的ATR熔断功能
        """
        try:
            # 获取足够的K线数据
            klines = self.get_kline_data(timeframe, period + 10)
            if len(klines) < period:
                return 0.0
            
            true_ranges = []
            
            for i in range(1, len(klines)):
                current = klines[i]
                previous = klines[i-1]
                
                # 计算True Range
                tr1 = current['high'] - current['low']
                tr2 = abs(current['high'] - previous['close'])
                tr3 = abs(current['low'] - previous['close'])
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            # 计算ATR（简单移动平均）
            if len(true_ranges) >= period:
                atr = sum(true_ranges[-period:]) / period
                return atr
            
            return 0.0
            
        except Exception as e:
            logger.log_error(f"计算ATR失败: {e}")
            return 0.0
    
    def check_price_jump(self, window_minutes: int = 30, factor: float = 2.0) -> Dict[str, Any]:
        """
        检查价格跳跃情况
        
        用于解套策略的跳跃熔断功能
        """
        try:
            # 获取短期K线数据
            klines = self.get_kline_data('1m', window_minutes + 5)
            if len(klines) < window_minutes:
                return {'is_jump': False, 'factor': 0.0}
            
            # 计算窗口内价格变化
            window_klines = klines[-window_minutes:]
            start_price = window_klines[0]['open']
            end_price = window_klines[-1]['close']
            max_price = max([k['high'] for k in window_klines])
            min_price = min([k['low'] for k in window_klines])
            
            # 计算价格变化幅度
            upward_move = (max_price - start_price) / start_price
            downward_move = (start_price - min_price) / start_price
            max_move = max(upward_move, downward_move)
            
            # 获取策略配置的add_interval_pct作为基准
            recovery_config = self.config.get('recovery', {})
            grid_config = recovery_config.get('grid', {})
            add_interval_pct = grid_config.get('add_interval_pct', 0.04)
            
            # 判断是否为跳跃
            threshold = add_interval_pct * factor
            is_jump = max_move > threshold
            
            return {
                'is_jump': is_jump,
                'factor': max_move / add_interval_pct if add_interval_pct > 0 else 0.0,
                'max_move': max_move,
                'threshold': threshold,
                'window_minutes': window_minutes
            }
            
        except Exception as e:
            logger.log_error(f"检查价格跳跃失败: {e}")
            return {'is_jump': False, 'factor': 0.0}
    
    def check_kline_filters(self, side: str, add_interval_pct: float) -> Dict[str, Any]:
        """
        检查K线确认过滤条件
        
        F1: 实体占比过滤 - 实体长度 >= 总区间 * body_min_frac
        F2: 影线比例过滤 - max(上影线, 下影线) <= 实体长度 * wick_to_body_max
        F3: 跟进确认窗口 - 确保价格在指定窗口内持续朝有利方向移动
        """
        try:
            recovery_config = self.config.get('recovery', {})
            confirm_config = recovery_config.get('confirm', {})
            filters = confirm_config.get('filters', {})
            kline_tf = confirm_config.get('kline', '15m')
            
            # 获取参数
            body_min_frac = filters.get('body_min_frac_of_interval', 0.25)
            wick_to_body_max = filters.get('wick_to_body_max', 2.0)
            followthrough_window = filters.get('followthrough_window_min', 15)
            
            # 获取K线数据
            klines = self.get_kline_data(kline_tf, 5)
            if len(klines) < 2:
                return {'passed': False, 'reason': 'K线数据不足'}
            
            latest_kline = klines[-1]
            open_price = latest_kline['open']
            close_price = latest_kline['close']
            high_price = latest_kline['high']
            low_price = latest_kline['low']
            
            # F1: 实体占比过滤
            total_range = high_price - low_price
            body_length = abs(close_price - open_price)
            body_ratio = body_length / total_range if total_range > 0 else 0
            
            required_body_ratio = body_min_frac * add_interval_pct
            f1_passed = body_ratio >= required_body_ratio
            
            # F2: 影线比例过滤
            upper_wick = high_price - max(open_price, close_price)
            lower_wick = min(open_price, close_price) - low_price
            max_wick = max(upper_wick, lower_wick)
            
            max_allowed_wick = body_length * wick_to_body_max
            f2_passed = max_wick <= max_allowed_wick
            
            # F3: 跟进确认窗口（简化实现）
            # 检查K线方向是否与交易方向一致
            is_bullish = close_price > open_price
            direction_match = (side == "long" and is_bullish) or (side == "short" and not is_bullish)
            f3_passed = direction_match
            
            # 综合判断
            all_passed = f1_passed and f2_passed and f3_passed
            
            return {
                'passed': all_passed,
                'f1_body_ratio': f1_passed,
                'f2_wick_ratio': f2_passed,
                'f3_direction': f3_passed,
                'details': {
                    'body_ratio': body_ratio,
                    'required_body_ratio': required_body_ratio,
                    'max_wick': max_wick,
                    'max_allowed_wick': max_allowed_wick,
                    'direction_match': direction_match
                }
            }
            
        except Exception as e:
            logger.log_error(f"检查K线过滤失败: {e}")
            return {'passed': False, 'reason': f'过滤检查出错: {e}'}
    
    def get_recent_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近成交记录"""
        try:
            trades = self.platform.get_recent_trades(self.symbol, limit)
            if not trades:
                return []
            
            formatted_trades = []
            for trade in trades:
                formatted_trades.append({
                    'id': trade.get('id'),
                    'price': float(trade.get('price', 0)),
                    'quantity': float(trade.get('qty', 0)),
                    'time': int(trade.get('time', 0)),
                    'is_buyer_maker': trade.get('isBuyerMaker', False)
                })
            
            return formatted_trades
            
        except Exception as e:
            logger.log_error(f"获取成交记录失败: {e}")
            return []
    
    def calculate_optimal_quantity(self, base_qty: float, available_balance: float, 
                                 price: float, leverage: float = 1.0) -> float:
        """
        计算最优交易数量
        
        考虑因素：
        1. 策略配置的基础数量
        2. 账户可用余额限制
        3. 杠杆倍数
        4. 交易所最小交易单位
        """
        try:
            # 获取交易对信息
            exchange_info = self.platform.get_exchange_info(self.symbol)
            if not exchange_info:
                return base_qty
            
            # 获取最小交易单位
            min_qty = float(exchange_info.get('min_quantity', 0.001))
            step_size = float(exchange_info.get('step_size', 0.001))
            
            # 计算可用资金限制下的最大数量
            required_margin = base_qty * price / leverage
            if required_margin > available_balance:
                max_affordable_qty = (available_balance * leverage) / price
                actual_qty = min(base_qty, max_affordable_qty)
            else:
                actual_qty = base_qty
            
            # 确保满足最小交易单位
            if actual_qty < min_qty:
                logger.log_warning(f"计算数量{actual_qty}小于最小单位{min_qty}")
                return 0.0
            
            # 按步长调整
            adjusted_qty = (actual_qty // step_size) * step_size
            
            return max(adjusted_qty, min_qty)
            
        except Exception as e:
            logger.log_error(f"计算最优数量失败: {e}")
            return base_qty
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """转换时间框架格式"""
        # 转换为Binance API格式
        conversion_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
        
        return conversion_map.get(timeframe, timeframe)
    
    def get_adapter_status(self) -> Dict[str, Any]:
        """获取适配器状态信息"""
        try:
            current_price = self.get_current_price()
            balance_info = self.get_account_balance()
            
            return {
                'symbol': self.symbol,
                'current_price': current_price,
                'balance': balance_info,
                'cache_items': len(self.price_cache),
                'platform_connected': self.platform.is_connected() if hasattr(self.platform, 'is_connected') else True
            }
            
        except Exception as e:
            logger.log_error(f"获取适配器状态失败: {e}")
            return {'error': str(e)}