# core/domain/enums.py
from enum import Enum

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"

class PositionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"

class TradeAction(Enum):
    OPEN_POSITION = "open_position"
    CLOSE_POSITION = "close_position"
    ADD_POSITION = "add_position"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
