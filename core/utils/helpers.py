# core/utils/helpers.py
from typing import Dict, Any, Optional
from decimal import Decimal
from core.domain.enums import Direction, PositionField

def get_pos_dict(position: Optional[dict] = None,
                 state: Optional[dict] = None,
                 direction: Optional[str] = None) -> Dict[str, Any]:
    if isinstance(position, dict):
        if direction in (Direction.LONG, Direction.SHORT) and direction in position:
            return position.get(direction) or {}
        if any(k in position for k in (PositionField.QTY, PositionField.AVG_PRICE, PositionField.ADD_TIMES, PositionField.HEDGE_LOCKED, PositionField.OPPOSITE_QTY)):
            return position
    if isinstance(state, dict) and direction in (Direction.LONG, Direction.SHORT):
        return state.get(direction) or {}
    return {}

def get_equal_eps(config: Optional[dict], default: str = "0.01") -> Decimal:
    try:
        v = ((config or {}).get("hedge") or {}).get("equal_eps", None)
        return Decimal(str(v)) if v is not None else Decimal(default)
    except Exception:
        return Decimal(default)
