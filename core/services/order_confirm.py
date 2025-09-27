"""
订单确认逻辑：确认下单后是否成交（order query -> trade list -> position fallback -> REST兜底）
移植自 old/execute/strategy_executor.py::_confirm_filled，做了轻量适配。
"""
import time
from typing import Tuple, Optional, Any
from core.domain.enums import Direction

from core.logger import logger
from core.state_store import load_state
from core.platform.base import ExchangeIf
import os

_VERBOSE = bool(os.environ.get("CONFIRM_VERBOSE") in ("1", "true", "True"))


def _parse_order_payload(od: dict):
    if not isinstance(od, dict):
        return None, None, None
    status = str(od.get("status", "")).upper()
    q = od.get("executedQty")
    if q is None:
        q = od.get("cumQty")
    px = od.get("avgPrice")
    try:
        qf = float(q) if q is not None else 0.0
    except Exception:
        qf = 0.0
    try:
        pxf = float(px) if px is not None else None
        if pxf is not None and pxf <= 0:
            pxf = None
    except Exception:
        pxf = None
    return status, qf, pxf


def _sum_trades_for_order(platform: ExchangeIf, sym: str, order_id: Any):
    # Try to call platform-specific user trades endpoint if available
    try:
        getter = getattr(platform, "get_user_trades", None)
        if not callable(getter):
            return 0.0, None
        # try symbol+orderId or orderId alone depending on adapter signature
        try:
            arr = getter(sym, order_id)
        except TypeError:
            try:
                arr = getter(order_id)
            except Exception:
                return 0.0, None
        if not isinstance(arr, (list, dict)):
            return 0.0, None
        # normalize to list
        if isinstance(arr, dict) and "data" in arr:
            items = arr.get("data") or []
        else:
            items = arr
        if not items:
            return 0.0, None
        tot_q = 0.0
        vwap_num = 0.0
        for it in items:
            if not isinstance(it, dict):
                continue
            try:
                q = float((it.get("qty") or it.get("quantity") or it.get("qty_base") or 0))
                p = float((it.get("price") or it.get("avgPrice") or it.get("priceExec") or 0))
            except Exception:
                continue
            if q > 0:
                tot_q += q
                vwap_num += q * p if p > 0 else 0.0
        vwap = (vwap_num / tot_q) if tot_q > 0 else None
        return tot_q, (vwap if (vwap and vwap > 0) else None)
    except Exception:
        return 0.0, None


def confirm_filled(platform: ExchangeIf,
                   symbol: str,
                   direction: str | Direction,
                   expect_qty: float,
                   hint_order_id: Optional[str] = None,
                   max_secs: float = 2.5,
                   mode: str = "open") -> Tuple[bool, float, Optional[float]]:
    """确认成交，返回 (ok, filled_qty, avg_price)"""
    _PLAN = float(expect_qty)
    _EPS = 1e-9

    def _clamp(q) -> float:
        try:
            return max(0.0, min(float(q), _PLAN * (1.0 + 1e-6)))
        except Exception:
            return 0.0

    def _try_order(order_id):
        if not order_id:
            return None
        # Prefer adapter get_order or module-level coinw fallback
        try:
            od = None
            getter = getattr(platform, "get_order", None)
            if callable(getter):
                try:
                    od = getter(order_id)
                except TypeError:
                    try:
                        od = getter(symbol, order_id)
                    except Exception:
                        od = None
            if not od:
                return None
            # adapt payload: support dict with data or direct order dict
            payload = od.get("data") if isinstance(od, dict) and "data" in od else od
            payload_dict = payload if isinstance(payload, dict) else {}
            st, q_exec, px = _parse_order_payload(payload_dict)
            if q_exec > _EPS:
                return True, _clamp(q_exec), px
            # Even if order status is not marked as FILLED, try to aggregate trades for the order
            try:
                try:
                    if isinstance(payload, dict):
                        oid = int(payload.get("orderId") or order_id)
                    else:
                        oid = order_id
                except Exception:
                    oid = order_id
                qt, vwap = _sum_trades_for_order(platform, symbol, oid)
                if qt > _EPS:
                    return True, _clamp(qt), (vwap if vwap is not None else px)
            except Exception:
                pass
        except Exception:
            return None
        return None

    def _try_position():
        # Try platform position endpoint first, then coinw fallback
        try:
            pos = None
            getter_pos = getattr(platform, "get_position", None)
            getter_positions = getattr(platform, "get_positions", None)
            if callable(getter_pos):
                try:
                    pos = getter_pos(symbol)
                except Exception:
                    pos = None
            elif callable(getter_positions):
                try:
                    pos = getter_positions(symbol)
                except Exception:
                    pos = None

            now_q = 0.0
            if pos and isinstance(pos, dict):
                try:
                    # support two shapes:
                    # 1) single-position dict with 'qty' (returned by get_position)
                    # 2) {'long': {...}, 'short': {...}} (returned by get_positions)
                    if "qty" in pos and not ("long" in pos or "short" in pos):
                        now_q = float(pos.get("qty") or 0)
                    else:
                        longp = pos.get("long") or {}
                        shortp = pos.get("short") or {}
                        # use normalized direction
                        if dnorm.upper() == "LONG":
                            now_q = float(longp.get("qty") or 0)
                        else:
                            now_q = float(shortp.get("qty") or 0)
                except Exception:
                    now_q = 0.0
            # debug logs for position path
            if _VERBOSE:
                try:
                    logger.log_info(f"[DEBUG confirm_filled] pos={pos} now_q={now_q} dnorm={dnorm}")
                except Exception:
                    pass

            if mode == "open":
                st0 = load_state()
                base = 0.0
                try:
                    side_attr = getattr(st0, direction.lower())
                    base = float(getattr(side_attr, "qty", 0) or 0)
                except Exception:
                    base = 0.0
                delta = max(0.0, now_q - base)
                if _VERBOSE:
                    try:
                        logger.log_info(f"[DEBUG confirm_filled] base={base} delta={delta} expect={expect_qty}")
                    except Exception:
                        pass
                if delta >= float(expect_qty) * 0.5:
                    return True, _clamp(delta), None
            else:
                if now_q <= max(1e-8, float(expect_qty) * 0.2):
                    return True, _clamp(expect_qty), None
        except Exception:
            pass
        return None

    # main polling loop
    deadline = time.time() + float(max_secs)
    # normalize direction (accept enum or string)
    try:
        dnorm = (direction.value if isinstance(direction, Direction) else str(direction)).lower()
    except Exception:
        dnorm = str(direction).lower()

    while time.time() < deadline:
        # try by order id first
        if hint_order_id:
            try:
                res = _try_order(hint_order_id)
                if isinstance(res, tuple):
                    return res
            except Exception:
                pass
        # try by position/trade fallback
        try:
            res = _try_position()
            if isinstance(res, tuple):
                return res
        except Exception:
            pass
        time.sleep(0.2)
    return False, 0.0, None
