from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_DOWN
from core.domain.enums import Direction, PositionField
from core.state_store import load_state, save_state
from core.domain.models import AccountState, PositionState
from core.config_loader import load_config
from core.logger import logger

class StateManager:
    def __init__(self, account: Optional[str] = None):
        self.account = account

    def get_state(self) -> AccountState:
        return load_state(self.account)

    def save_state(self, state: AccountState):
        save_state(self.account, state)

    def update_state_bulk(self, update_dict: dict):
        state = self.get_state()
        changed_any = False
        _QTY_KEYS = {PositionField.QTY, PositionField.LAST_QTY, PositionField.OPPOSITE_QTY}
        _PRICE_KEYS = {PositionField.AVG_PRICE, PositionField.LAST_FILL_PRICE, PositionField.LAST_ENTRY_PRICE}

        def _q_qty(v):
            try:
                return float(Decimal(str(v if v is not None else 0)).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN))
            except Exception:
                return float(v or 0)

        def _q_px(v):
            try:
                return float(Decimal(str(v if v is not None else 0)).quantize(Decimal("0.0001"), rounding=ROUND_DOWN))
            except Exception:
                return float(v or 0)

        for key, value in update_dict.items():
            if key not in (Direction.LONG, Direction.SHORT):
                old_value = getattr(state, key, None)
                if isinstance(old_value, dict) and isinstance(value, dict):
                    merged = {**old_value, **value}
                    if merged != old_value:
                        setattr(state, key, merged)
                        changed_any = True
                        logger.log_info(f"[DEBUG] 顶层字典合并：{key} += {value}")
                else:
                    if old_value != value:
                        setattr(state, key, value)
                        changed_any = True
                        logger.log_info(f"[DEBUG] 顶层字段变更：{key}: {old_value} → {value}")
                continue
            pos: PositionState = getattr(state, key)
            if not isinstance(value, dict):
                logger.log_warning(f"[WARN] update_state_bulk: {key} 的值不是 dict，已跳过。")
                continue
            for sub_key, sub_value in value.items():
                _new = sub_value
                if sub_key in _QTY_KEYS:
                    _new = _q_qty(sub_value)
                elif sub_key in _PRICE_KEYS:
                    _new = _q_px(sub_value)
                old_value = getattr(pos, sub_key, None)
                if old_value != _new:
                    setattr(pos, sub_key, _new)
                    changed_any = True
                    logger.log_info(f"[DEBUG] 更新 state[{key}].{sub_key}: {old_value} → {_new}")
        if changed_any:
            self.save_state(state)
        else:
            logger.log_info("[DEBUG] update_state_bulk 未检测到字段变化（未写入）。")
        return state

    def reset_direction_state(self, direction: str):
        state = self.get_state()
        import os
        _cfg_path = os.getenv("CONFIG_PATH")
        try:
            if _cfg_path:
                _cfg = load_config(_cfg_path)
            else:
                _cfg = {}
        except Exception:
            _cfg = {}
        try:
            if isinstance(_cfg, dict):
                _fq = float(((_cfg.get(direction) or {}).get("first_qty")) or 0)
            else:
                _fq = 0.0
        except Exception:
            _fq = 0.0
        pos = PositionState(
            qty=0,
            avg_price=0,
            add_times=0,
            last_qty=_fq,
            last_add_time=None,
            hedge_locked=False,
            hedge_stop=False,
            locked_profit=0
        )
        setattr(state, direction, pos)
        self.save_state(state)
        return state
