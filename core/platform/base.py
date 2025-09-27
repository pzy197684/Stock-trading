# core/platform/base.py
# 功能：定义交易平台接口的抽象类
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List, Union
from enum import Enum
import json

class OrderStatus(Enum):
    """统一订单状态枚举"""
    PENDING = "pending"         # 挂单中
    FILLED = "filled"          # 完全成交
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    CANCELLED = "cancelled"    # 已取消
    REJECTED = "rejected"      # 被拒绝
    UNKNOWN = "unknown"        # 未知状态

class OrderType(Enum):
    """统一订单类型枚举"""
    MARKET = "market"          # 市价单
    LIMIT = "limit"           # 限价单
    STOP = "stop"             # 止损单
    STOP_LIMIT = "stop_limit" # 限价止损单

class OrderSide(Enum):
    """统一订单方向枚举"""
    BUY = "buy"               # 买入
    SELL = "sell"             # 卖出

def create_error_response(reason: str, code: Optional[str] = None, raw: Any = None) -> Dict[str, Any]:
    """创建标准错误响应"""
    return {
        "error": True,
        "reason": reason,
        "code": code,
        "raw": raw,
        "timestamp": None  # 可由具体实现填充
    }

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """创建标准成功响应"""
    response = {"error": False, "timestamp": None}
    response.update(data)
    return response

class ExchangeIf(ABC):
    """
    交易平台统一接口抽象类
    
    设计原则：
    1. 所有方法返回标准格式的dict，异常情况返回error dict而不抛出异常
    2. 字段名使用项目通用domain名称（orderId/status/qty/avgPrice等）
    3. 支持平台差异化，但保持接口统一
    4. 提供足够的元信息供上层业务逻辑使用
    """
    
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret
        self.extra_params = kwargs
        self._initialized = False

    @abstractmethod
    def name(self) -> str:
        """平台名称（如'binance', 'coinw', 'okx'）"""
        raise NotImplementedError()

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """
        平台能力描述
        返回格式：{
            "hedge_support": bool,        # 是否支持对冲
            "position_mode": str,         # "single" or "both" 
            "unit_type": str,            # "coin" or "contract"
            "min_order_size": float,     # 最小下单数量
            "price_precision": int,      # 价格精度
            "quantity_precision": int,   # 数量精度
            "supported_order_types": List[str],  # 支持的订单类型
            "rate_limit": Dict[str, int] # 速率限制信息
        }
        """
        raise NotImplementedError()

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        成功返回：{
            "error": False,
            "balance": Dict[str, float],     # 资产余额
            "available": Dict[str, float],   # 可用余额  
            "frozen": Dict[str, float],      # 冻结余额
            "equity": float,                 # 账户权益
            "margin_ratio": float           # 保证金率（期货）
        }
        """
        raise NotImplementedError()

    @abstractmethod
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        获取指定交易对的仓位信息
        成功返回：{
            "error": False,
            "symbol": str,
            "qty": float,              # 持仓数量（净持仓）
            "avgPrice": float,         # 平均价格
            "unrealizedPnl": float,    # 未实现盈亏
            "side": str,              # "long", "short", "none"
            "leverage": float,        # 杠杆倍数
            "margin": float          # 占用保证金
        }
        """
        raise NotImplementedError()

    @abstractmethod
    def get_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取所有或指定交易对的仓位信息
        成功返回：{
            "error": False,
            "positions": List[Dict] 或 Dict[str, Dict]  # 仓位列表或字典
        }
        对于支持双向持仓的平台，单个仓位可能包含long/short结构
        """
        raise NotImplementedError()

    @abstractmethod
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        查询单个订单详情
        成功返回：{
            "error": False,
            "orderId": str,
            "symbol": str,
            "status": str,            # 使用OrderStatus枚举值
            "side": str,             # "buy" or "sell"
            "type": str,             # "market", "limit", etc.
            "qty": float,            # 订单数量
            "price": float,          # 订单价格（限价单）
            "filledQty": float,      # 已成交数量
            "avgPrice": float,       # 平均成交价格
            "commission": float,     # 手续费
            "timestamp": int,        # 订单时间戳
            "updateTime": int        # 最后更新时间
        }
        """
        raise NotImplementedError()

    @abstractmethod
    def get_user_trades(self, symbol: str, order_id: Optional[str] = None, 
                       since: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        查询用户成交记录
        成功返回：{
            "error": False,
            "trades": List[{
                "id": str,
                "orderId": str,
                "symbol": str,
                "qty": float,
                "price": float,
                "side": str,             # "buy" or "sell"
                "isBuyer": bool,
                "commission": float,
                "timestamp": int
            }]
        }
        """
        raise NotImplementedError()

    def to_instrument(self, symbol: str) -> str:
        """
        将统一symbol转换为平台内部instrument表示
        默认原样返回，具体平台可重写
        """
        return symbol

    def from_instrument(self, instrument: str) -> str:
        """
        将平台内部instrument转换为统一symbol
        默认原样返回，具体平台可重写
        """
        return instrument

    @abstractmethod
    def place_order(self, order_req: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行下单请求
        入参格式：{
            "symbol": str,           # 交易对
            "side": str,            # "buy" or "sell"
            "type": str,            # "market", "limit", etc.
            "qty": float,           # 订单数量
            "price": float,         # 订单价格（限价单必填）
            "timeInForce": str,     # 订单生效时间（可选）
            "clientOrderId": str    # 客户端订单ID（可选）
        }
        
        成功返回：{
            "error": False,
            "orderId": str,
            "clientOrderId": str,
            "status": str,          # 订单状态
            "symbol": str,
            "side": str,
            "type": str,
            "qty": float,
            "price": float,
            "filledQty": float,     # 已成交数量
            "avgPrice": float,      # 平均成交价（如有）
            "timestamp": int
        }
        """
        raise NotImplementedError()

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        取消指定订单
        成功返回：{
            "error": False,
            "orderId": str,
            "status": str,          # 取消后状态
            "symbol": str
        }
        """
        raise NotImplementedError()

    def get_market_price(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场最新价格（可选实现）
        成功返回：{
            "error": False,
            "symbol": str,
            "price": float,
            "timestamp": int
        }
        """
        return create_error_response("get_market_price not implemented")

    def validate_order_request(self, order_req: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证订单请求格式（基础验证）
        子类可重写进行平台特定验证
        """
        required_fields = ["symbol", "side", "type", "qty"]
        missing = [f for f in required_fields if f not in order_req]
        if missing:
            return create_error_response(f"Missing required fields: {missing}")
        
        # 验证订单方向
        if order_req["side"] not in [OrderSide.BUY.value, OrderSide.SELL.value]:
            return create_error_response(f"Invalid order side: {order_req['side']}")
        
        # 验证数量
        try:
            qty = float(order_req["qty"])
            if qty <= 0:
                return create_error_response("Order quantity must be positive")
        except (ValueError, TypeError):
            return create_error_response("Invalid quantity format")
        
        # 限价单必须有价格
        if order_req["type"] == OrderType.LIMIT.value and "price" not in order_req:
            return create_error_response("Limit order requires price")
        
        return create_success_response({"valid": True})

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value: Any, default: int = 0) -> int:
        """安全转换为整数"""
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _safe_str(self, value: Any, default: str = "") -> str:
        """安全转换为字符串"""
        try:
            return str(value) if value is not None else default
        except (ValueError, TypeError):
            return default
