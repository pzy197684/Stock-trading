from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dataclasses import dataclass, field
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

@dataclass
class AddHistory:
    """记录快速加仓的时间戳"""
    timestamps: List[int] = field(default_factory=list)
    fast_add_paused_until: int = 0

    def append(self, ts: int, max_len: int = 5):
        self.timestamps.append(ts)
        self.timestamps = [int(x) for x in self.timestamps if isinstance(x, (int, float))][-max_len:]


# 持仓方向状态
@dataclass
class PositionState:
    """持仓方向状态"""
    qty: float = 0
    avg_price: float = 0
    add_times: int = 0
    last_add_time: Optional[float] = None
    hedge_locked: bool = False
    hedge_stop: bool = False
    locked_profit: float = 0
    round: int = 0
    last_qty: float = 0
    opposite_qty: float = 0
    last_entry_price: float = 0
    last_fill_price: float = 0
    last_fill_ts: float = 0
    last_open_ts: float = 0
    fast_add_paused_until: float = 0
    cooldown_until: float = 0

# 账户指标
@dataclass
class Metrics:
    """账户指标"""
    nv_prev: float = 0.0
    last_snapshot_date: str = ""

# 账户整体状态
@dataclass
class AccountState:
    """账户整体状态"""
    long: PositionState = field(default_factory=PositionState)
    short: PositionState = field(default_factory=PositionState)
    metrics: Metrics = field(default_factory=Metrics)
    pause_until: Optional[float] = None
    schema_hydrated: dict = field(default_factory=dict)
    backfill_done: dict = field(default_factory=dict)
    # 新增UI友好的元数据字段
    metadata: dict = field(default_factory=lambda: {
        "created_at": "",
        "updated_at": "", 
        "version": "2.0.0",
        "account": "",
        "platform": "",
        "strategy": "",
        "status": "initialized"
    })