
# core/domain/enums.py
# 功能：定义各种枚举类型，如订单类型、交易方向等
from enum import Enum

# 方向常量
class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"

# 持仓字段常量
class PositionField(str, Enum):
    QTY = "qty"
    AVG_PRICE = "avg_price"
    ADD_TIMES = "add_times"
    LAST_ADD_TIME = "last_add_time"
    HEDGE_LOCKED = "hedge_locked"
    HEDGE_STOP = "hedge_stop"
    LOCKED_PROFIT = "locked_profit"
    OPPOSITE_QTY = "opposite_qty"
    ROUND = "round"
    LAST_QTY = "last_qty"
    LAST_ENTRY_PRICE = "last_entry_price"
    LAST_FILL_PRICE = "last_fill_price"
    LAST_FILL_TS = "last_fill_ts"
    LAST_OPEN_TS = "last_open_ts"
    FAST_ADD_PAUSED_UNTIL = "fast_add_paused_until"
    COOLDOWN_UNTIL = "cooldown_until"
    ADD_HISTORY = "add_history"
    
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

# 平台名称常量
class Platform(str, Enum):
    BINANCE = "binance"
    COINW = "coinw"
    OKX = "okx"

# 配置键常量
class ConfigKey(str, Enum):
    ACCOUNTS = "accounts"
    STRATEGIES = "strategies"
    PLATFORM = "platform"
    DEFAULT_PLATFORM = "default_platform"
    API_KEY = "api_key"
    API_SECRET = "api_secret"
    SYMBOL = "symbol"
    STRATEGY_NAME = "strategy_name"
    NAME = "name"
    PARAMS = "params"
    RISK_CONTROL = "risk_control"
    PROFIT_EXTRACT = "profit_extract"
    ENABLED = "enabled"
    HEDGE_MODE = "hedge_mode"

# 订单状态常量
class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    UNKNOWN = "unknown"
    NEW = "NEW"

# 位置侧常量
class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

# 响应字段常量
class ResponseField(str, Enum):
    CODE = "code"
    ORDER_ID = "orderId"
    DATA = "data"
    VALUE = "value"
    ERROR = "error"
    REASON = "reason"
    RAW = "raw"
    TIMESTAMP = "timestamp"

# 环境变量键常量
class EnvKey(str, Enum):
    ACCOUNT = "ACCOUNT"
    ACCOUNTS_DIR = "ACCOUNTS_DIR"
    API_KEY_ENV = "API_KEY"
    API_SECRET_ENV = "API_SECRET"

# 默认值常量
class DefaultValue(str, Enum):
    ACCOUNT = "BN8891"
    ACCOUNTS_DIR = "accounts"
    PLATFORM = "coinw"
    STRATEGY_NAME = "martingale_v3"
    STRATEGY_DISPLAY_NAME = "Martingale Strategy"
    MOCK_API_KEY = "mock"
    MOCK_API_SECRET = "mock"
    MOCK_PLATFORM = "Mock"
    LOG_CATEGORY = "stock_trading"

# 时间常量
class TimeConstant(str, Enum):
    FAST_ADD_WINDOW_SEC = "fast_add_window_sec"
    FAST_ADD_PAUSE_SEC = "fast_add_pause_sec"
