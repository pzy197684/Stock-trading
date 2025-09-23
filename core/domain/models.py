# core/domain/models.py
from typing import Optional
from dataclasses import dataclass
from core.domain.enums import OrderSide, OrderType, PositionStatus

@dataclass
class OrderReq:
    symbol: str
    quantity: float
    price: float
    side: OrderSide
    order_type: OrderType
    timestamp: Optional[int] = None  # 时间戳，可选

@dataclass
class OrderResp:
    order_id: str
    status: str
    order_details: OrderReq

@dataclass
class PositionSnapshot:
    symbol: str
    qty: float
    avg_price: float
    status: PositionStatus
