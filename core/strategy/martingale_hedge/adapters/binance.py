# -*- coding: utf-8 -*-
# core/strategy/martingale_hedge/adapters/binance.py
# 功能：马丁对冲策略的Binance交易所适配器

from core.platform.base import ExchangeIf, OrderSide, OrderType, OrderStatus, create_success_response, create_error_response
from core.logger import logger
from core.utils.decimal_ext import Decimal, ZERO
from typing import Dict, Any, Optional, List, Union
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

class BinanceMartingaleAdapter:
    """
    Binance交易所马丁对冲策略适配器
    
    负责：
    1. 与Binance API交互
    2. 订单确认和成交验证
    3. 持仓状态同步
    4. 错误处理和异常恢复
    """
    
    def __init__(self, exchange_if: ExchangeIf):
        self.exchange = exchange_if
        self.base_url = "https://fapi.binance.com"
        
    def place_order(self, symbol: str, side: str, position_side: str, 
                   quantity: float, order_type: str = "MARKET",
                   price: Optional[float] = None) -> Dict[str, Any]:
        """
        下单接口 - 统一封装Binance期货下单
        
        Args:
            symbol: 交易对
            side: BUY/SELL
            position_side: LONG/SHORT
            quantity: 数量
            order_type: 订单类型
            price: 价格（限价单需要）
            
        Returns:
            标准化响应格式
        """
        try:
            logger.log_info(f"🛒 Binance下单：{symbol} {side}/{position_side} qty={quantity} type={order_type}")
            
            # 构建订单参数
            params = {
                "symbol": symbol,
                "side": side,
                "positionSide": position_side,
                "quantity": str(quantity),
                "type": order_type,
                "timestamp": int(time.time() * 1000),
                "recvWindow": 5000
            }
            
            if order_type == "LIMIT" and price:
                params["price"] = str(price)
                params["timeInForce"] = "GTC"
            
            # 发送请求
            response = self._signed_request("POST", "/fapi/v1/order", params)
            
            if response.get("error"):
                logger.log_error(f"❌ Binance下单失败：{response}")
                return response
            
            # 解析响应
            order_id = response.get("orderId")
            status = response.get("status", "").upper()
            executed_qty = float(response.get("executedQty", 0))
            avg_price = float(response.get("avgPrice", 0)) if response.get("avgPrice") else None
            
            logger.log_info(f"✅ Binance下单成功：orderId={order_id} status={status} executedQty={executed_qty}")
            
            return create_success_response({
                "orderId": order_id,
                "status": status,
                "executedQty": executed_qty,
                "avgPrice": avg_price,
                "symbol": symbol,
                "side": side,
                "positionSide": position_side,
                "quantity": quantity
            })
            
        except Exception as e:
            logger.log_error(f"❌ Binance下单异常：{e}")
            return create_error_response(f"下单异常: {e}", raw=str(e))
    
    def confirm_order_filled(self, symbol: str, direction: str, order_id: Optional[str],
                           expected_qty: float, max_wait_seconds: float = 3.0) -> tuple[bool, float, Optional[float]]:
        """
        确认订单成交 - 从928项目移植的成交确认逻辑
        
        Args:
            symbol: 交易对
            direction: long/short
            order_id: 订单ID（可选）
            expected_qty: 预期成交量
            max_wait_seconds: 最大等待时间
            
        Returns:
            (成交确认, 实际成交量, 成交均价)
        """
        try:
            deadline = time.time() + max_wait_seconds
            position_side = direction.upper()
            
            # 获取确认前基线持仓（用于增量判断）
            baseline_qty = self._get_baseline_position_qty(symbol, position_side)
            
            while time.time() < deadline:
                # 优先用订单查询
                if order_id:
                    order_result = self._try_confirm_by_order(order_id, expected_qty)
                    if order_result[0]:  # 确认成功
                        return order_result
                
                # 降级用持仓确认
                position_result = self._try_confirm_by_position(symbol, position_side, 
                                                              expected_qty, baseline_qty)
                if position_result[0]:  # 确认成功  
                    return position_result
                
                time.sleep(0.2)  # 短暂等待后重试
            
            logger.log_warning(f"⚠️ 订单成交确认超时：symbol={symbol} orderId={order_id}")
            return (False, 0.0, None)
            
        except Exception as e:
            logger.log_error(f"❌ 订单成交确认异常：{e}")
            return (False, 0.0, None)
    
    def get_position_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取持仓信息 - 返回多空持仓详情
        
        Returns:
            {
                "error": False,
                "long": {"qty": float, "avg_price": float},
                "short": {"qty": float, "avg_price": float},
                "_raw": {...}  # 原始响应
            }
        """
        try:
            params = {
                "symbol": symbol,
                "timestamp": int(time.time() * 1000),
                "recvWindow": 5000
            }
            
            response = self._signed_request("GET", "/fapi/v2/positionRisk", params)
            
            if response.get("error"):
                logger.log_error(f"❌ 获取持仓失败：{response}")
                return response
            
            # 解析持仓数据
            positions = response if isinstance(response, list) else [response]
            long_pos = {"qty": 0.0, "avg_price": 0.0}
            short_pos = {"qty": 0.0, "avg_price": 0.0}
            
            for pos in positions:
                if pos.get("symbol") == symbol:
                    position_side = pos.get("positionSide", "").upper()
                    position_amt = float(pos.get("positionAmt", 0))
                    entry_price = float(pos.get("entryPrice", 0))
                    
                    if position_side == "LONG" and position_amt > 0:
                        long_pos = {"qty": position_amt, "avg_price": entry_price}
                    elif position_side == "SHORT" and position_amt < 0:
                        short_pos = {"qty": abs(position_amt), "avg_price": entry_price}
            
            return create_success_response({
                "long": long_pos,
                "short": short_pos,
                "_raw": response
            })
            
        except Exception as e:
            logger.log_error(f"❌ 获取持仓异常：{e}")
            return create_error_response(f"获取持仓异常: {e}", raw=str(e))
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        获取当前市场价格
        
        Returns:
            {
                "error": False,
                "price": float,
                "symbol": str,
                "timestamp": int
            }
        """
        try:
            # 使用24hr ticker API获取最新价格
            url = f"{self.base_url}/fapi/v1/ticker/24hr"
            params = {"symbol": symbol}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return create_error_response(f"HTTP错误: {response.status_code}")
            
            data = response.json()
            price = float(data.get("lastPrice", 0))
            
            if price <= 0:
                return create_error_response("无效价格数据")
            
            return create_success_response({
                "price": price,
                "symbol": symbol,
                "timestamp": int(time.time() * 1000)
            })
            
        except Exception as e:
            logger.log_error(f"❌ 获取价格异常：{e}")
            return create_error_response(f"获取价格异常: {e}", raw=str(e))
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        获取账户余额信息
        
        Returns:
            标准化账户信息
        """
        try:
            params = {
                "timestamp": int(time.time() * 1000),
                "recvWindow": 5000
            }
            
            response = self._signed_request("GET", "/fapi/v2/account", params)
            
            if response.get("error"):
                return response
            
            # 解析余额数据
            total_wallet_balance = float(response.get("totalWalletBalance", 0))
            total_unrealized_pnl = float(response.get("totalUnrealizedPnl", 0))
            available_balance = float(response.get("availableBalance", 0))
            
            return create_success_response({
                "balance": {"USDT": total_wallet_balance},
                "available": {"USDT": available_balance},
                "equity": total_wallet_balance + total_unrealized_pnl,
                "unrealized_pnl": total_unrealized_pnl,
                "margin_ratio": float(response.get("totalMaintMargin", 0))
            })
            
        except Exception as e:
            logger.log_error(f"❌ 获取账户余额异常：{e}")
            return create_error_response(f"获取账户余额异常: {e}", raw=str(e))

    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """撤销订单"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": int(time.time() * 1000),
                "recvWindow": 5000
            }
            
            response = self._signed_request("DELETE", "/fapi/v1/order", params)
            
            if response.get("error"):
                return response
            
            return create_success_response({
                "orderId": response.get("orderId"),
                "status": "CANCELLED",
                "symbol": symbol
            })
            
        except Exception as e:
            logger.log_error(f"❌ 撤销订单异常：{e}")
            return create_error_response(f"撤销订单异常: {e}", raw=str(e))

    # ============================================================================
    # 私有辅助方法
    # ============================================================================
    
    def _signed_request(self, method: str, endpoint: str, params: Dict) -> Dict[str, Any]:
        """发送签名请求"""
        try:
            # 构建查询字符串
            query_string = urlencode(params, doseq=True)
            
            # 生成签名
            signature = hmac.new(
                self.exchange.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # 添加签名
            params['signature'] = signature
            
            # 构建请求
            headers = {
                'X-MBX-APIKEY': self.exchange.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, data=params, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, params=params, headers=headers, timeout=10)
            else:
                return create_error_response(f"不支持的HTTP方法: {method}")
            
            # 检查HTTP状态
            if response.status_code != 200:
                return create_error_response(f"HTTP错误: {response.status_code}", 
                                           code=str(response.status_code), raw=response.text)
            
            # 解析JSON
            data = response.json()
            
            # 检查API错误
            if isinstance(data, dict) and "code" in data and data["code"] != 0:
                return create_error_response(data.get("msg", "API错误"), 
                                           code=str(data["code"]), raw=data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            return create_error_response(f"网络请求异常: {e}", raw=str(e))
        except Exception as e:
            return create_error_response(f"请求处理异常: {e}", raw=str(e))
    
    def _try_confirm_by_order(self, order_id: str, expected_qty: float) -> tuple[bool, float, Optional[float]]:
        """通过订单查询确认成交"""
        try:
            params = {
                "orderId": order_id,
                "timestamp": int(time.time() * 1000),
                "recvWindow": 5000
            }
            
            response = self._signed_request("GET", "/fapi/v1/order", params)
            
            if response.get("error"):
                return (False, 0.0, None)
            
            status = response.get("status", "").upper()
            executed_qty = float(response.get("executedQty", 0))
            avg_price = float(response.get("avgPrice", 0)) if response.get("avgPrice") else None
            
            # 检查是否有足够的成交量
            if executed_qty >= expected_qty * 0.5:  # 至少50%成交才认为确认
                return (True, min(executed_qty, expected_qty), avg_price)
            
            # 如果状态显示已成交但executedQty为0，尝试从成交记录获取
            if status in ("FILLED", "PARTIALLY_FILLED"):
                trade_qty, trade_price = self._get_trade_history(order_id)
                if trade_qty >= expected_qty * 0.5:
                    return (True, min(trade_qty, expected_qty), trade_price)
            
            return (False, 0.0, None)
            
        except Exception as e:
            logger.log_warning(f"⚠️ 订单确认查询异常：{e}")
            return (False, 0.0, None)
    
    def _try_confirm_by_position(self, symbol: str, position_side: str, 
                               expected_qty: float, baseline_qty: float) -> tuple[bool, float, Optional[float]]:
        """通过持仓确认成交"""
        try:
            position_info = self.get_position_info(symbol)
            
            if position_info.get("error"):
                return (False, 0.0, None)
            
            # 获取对应方向的持仓
            direction_key = "long" if position_side == "LONG" else "short"
            current_qty = position_info[direction_key]["qty"]
            
            # 计算增量
            delta = max(0, current_qty - baseline_qty)
            
            # 如果增量达到预期的50%以上，认为确认成功
            if delta >= expected_qty * 0.5:
                # 获取当前价格作为成交价格（近似）
                price_info = self.get_current_price(symbol)
                current_price = price_info.get("price") if not price_info.get("error") else None
                
                return (True, min(delta, expected_qty), current_price)
            
            return (False, 0.0, None)
            
        except Exception as e:
            logger.log_warning(f"⚠️ 持仓确认查询异常：{e}")
            return (False, 0.0, None)
    
    def _get_baseline_position_qty(self, symbol: str, position_side: str) -> float:
        """获取基线持仓数量（用于增量计算）"""
        try:
            position_info = self.get_position_info(symbol)
            if position_info.get("error"):
                return 0.0
            
            direction_key = "long" if position_side == "LONG" else "short"
            return position_info[direction_key]["qty"]
            
        except Exception:
            return 0.0
    
    def _get_trade_history(self, order_id: str) -> tuple[float, Optional[float]]:
        """获取订单成交记录"""
        try:
            params = {
                "orderId": order_id,
                "timestamp": int(time.time() * 1000),
                "recvWindow": 5000,
                "limit": 1000
            }
            
            response = self._signed_request("GET", "/fapi/v1/userTrades", params)
            
            if response.get("error") or not isinstance(response, list):
                return (0.0, None)
            
            total_qty = 0.0
            vwap_numerator = 0.0
            
            for trade in response:
                qty = float(trade.get("qty", 0))
                price = float(trade.get("price", 0))
                
                total_qty += qty
                if price > 0:
                    vwap_numerator += qty * price
            
            # 计算加权平均价格
            avg_price = (vwap_numerator / total_qty) if total_qty > 0 else None
            
            return (total_qty, avg_price)
            
        except Exception as e:
            logger.log_warning(f"⚠️ 获取成交记录异常：{e}")
            return (0.0, None)