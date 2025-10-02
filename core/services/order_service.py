# core/services/order_service.py
"""
订单服务：负责数量规整（lot rules）、有限重试下单与平仓封装。
该实现移植自 old/execute/order_executor.py 的核心逻辑，简化了通知与部分日志函数，使用 core.logger。
"""
import time
import random
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Any, Tuple, cast

import requests

from core.logger import logger
from core.domain.enums import Direction
from core.services.order_confirm import confirm_filled
from core.managers.state_manager import StateManager

# 简单缓存：交易所规则（LOT_SIZE）
_filters_cache = {}  # {symbol: {"step": Decimal, "min_qty": Decimal, "ts": int}}
_FILTERS_TTL = 60 * 60

def _fetch_lot_filters(symbol: str):
    """尝试获取交易对的最小步进/最小下单量；优先使用 CoinW 元数据，否则退回 Binance exchangeInfo。"""
    try:
        # Try CoinW instruments via core.platform.coinw if available
        from core.platform import coinw as _coinw  # type: ignore
        inst = _coinw.to_instrument(symbol)
        info = _coinw.get_instrument_info(inst)
        lot_size = info.get("oneLotSize") or 0.01
        min_lots = info.get("minSize") or 1
        step = Decimal(str(lot_size))
        min_qty = Decimal(str(lot_size)) * Decimal(str(min_lots))
        return {"step": step, "min_qty": min_qty, "ts": int(time.time())}
    except Exception:
        # Fallback to Binance public exchangeInfo
        try:
            url = f"https://fapi.binance.com/fapi/v1/exchangeInfo?symbol={symbol}"
            r = requests.get(url, timeout=(3.05, 10))
            if not r.ok:
                logger.log_error(f"❌ 获取 {symbol} 规则失败: {r.status_code} {r.text}")
                return None
            data = r.json()
            syms = data.get("symbols") or []
            if not syms:
                return None
            filters = syms[0].get("filters") or []
            lot = next((f for f in filters if f.get("filterType") in ("LOT_SIZE", "MARKET_LOT_SIZE")), None)
            if not lot:
                return None
            step = Decimal(str(lot.get("stepSize", "0.001")))
            min_qty = Decimal(str(lot.get("minQty", "0")))
            return {"step": step, "min_qty": min_qty}
        except Exception as e:
            logger.log_error(f"❌ 获取 {symbol} 规则异常: {e}")
            return None

def _get_lot_filters(symbol: str):
    now = int(time.time())
    ent = _filters_cache.get(symbol)
    if ent and (now - ent.get("ts", 0) < _FILTERS_TTL):
        return ent
    f = _fetch_lot_filters(symbol)
    if f:
        # cast to a mutable dict[Any, Any] to satisfy static typing for mixed value types
        f = cast(dict, f)
        f["ts"] = now
        _filters_cache[symbol] = f
    return _filters_cache.get(symbol)

def _normalize_qty(symbol: str, qty) -> Decimal:
    try:
        q = Decimal(str(qty))
    except Exception:
        return Decimal("0")
    if q <= 0:
        return Decimal("0")

    filters = _get_lot_filters(symbol)
    if not filters:
        q_norm = q.quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        logger.log_info(f"⚠️ 未获取到 {symbol} LOT_SIZE 规则，降级使用 6 位截断：{qty} -> {q_norm}")
        return q_norm

    _step = filters.get("step")
    _minq = filters.get("min_qty")
    try:
        step = Decimal(str(_step)) if _step is not None else Decimal("0.000001")
    except Exception:
        step = Decimal("0.000001")
    try:
        min_qty = Decimal(str(_minq)) if _minq is not None else Decimal("0")
    except Exception:
        min_qty = Decimal("0")
    if step <= 0:
        step = Decimal("0.000001")
    k = (q / step).to_integral_value(rounding=ROUND_DOWN)
    q_norm = (k * step).quantize(step, rounding=ROUND_DOWN)
    if min_qty and q_norm < min_qty:
        logger.log_error(f"❌ 归一化后数量低于最小下单量：{q_norm} < minQty({min_qty})")
        return Decimal("0")
    return q_norm


# =========================
# 重试判定与退避工具
# =========================
_RETRYABLE_CODES = {-1003, -1015, -1021, -1105}

def _is_retryable(resp, exc) -> Tuple[bool, str]:
    if exc is not None:
        if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError)):
            return True, f"{exc.__class__.__name__}"
        return False, f"{exc}"
    if isinstance(resp, dict):
        code = resp.get("code")
        msg = str(resp.get("msg", "")).lower()
        if isinstance(code, int) and code in _RETRYABLE_CODES:
            return True, f"code={code}"
        if any(k in msg for k in [
            "too many requests", "system busy", "service unavailable",
            "internal error", "timeout", "timestamp"
        ]):
            return True, f"msg={resp.get('msg','')}"
        st = resp.get("status")
        if isinstance(st, int) and 500 <= st <= 599:
            return True, f"http {st}"
        return False, resp.get("msg", "unknown error")
    s = str(resp).lower()
    if any(k in s for k in ["service unavailable", "internal error", "timeout"]):
        return True, f"text={resp}"
    return False, s or "unknown"


def place_order_with_retry(platform, symbol: str, side: str, positionSide: str, quantity, order_type: str, max_tries: int = 3):
    q_norm = _normalize_qty(symbol, quantity)
    if q_norm <= 0:
        logger.log_error(f"❌ 放弃下单：数量归一化失败或不足最小下单量。原始={quantity}")
        return {"error": True, "reason": "qty_normalize_failed", "orig_qty": quantity}

    BASE = 0.8
    CAP = 5.0

    for attempt in range(1, max_tries + 1):
        logger.log_info(f"🛰️ 下单尝试 {attempt}/{max_tries}: {symbol} {side} {positionSide} 数量={q_norm} 类型={order_type}")
        try:
            # Platform is expected to provide place_order(...) signature compatible with platform adapters
            response = platform.place_order({
                "instrument": platform.to_instrument(symbol) if hasattr(platform, "to_instrument") else symbol,
                "direction": positionSide.lower() if positionSide else side.lower(),
                "quantity": float(q_norm),
                "type": order_type
            })
        except Exception as e:
            retry, reason = _is_retryable(None, e)
            if retry and attempt < max_tries:
                delay = min(BASE * (2 ** (attempt - 1)) + random.uniform(0, BASE), CAP)
                logger.log_error(f"⏳ 下单失败（异常，可重试）：{e} → {delay:.2f}s 后重试")
                time.sleep(delay)
                continue
            logger.log_error(f"❌ 下单失败（异常，放弃）：{e}")
            return {"error": True, "reason": str(e), "retryable": retry}

        if isinstance(response, dict) and response.get("orderId"):
            logger.log_info(f"✅ 下单成功 - orderId={response.get('orderId')}")
            return response

        retry, reason = _is_retryable(response, None)
        if retry and attempt < max_tries:
            delay = min(BASE * (2 ** (attempt - 1)) + random.uniform(0, BASE), CAP)
            logger.log_error(f"⏳ 下单失败（可重试）：原因={reason} → {delay:.2f}s 后重试；原始响应: {response}")
            time.sleep(delay)
            continue

        error_msg = response.get("msg", "未知错误") if isinstance(response, dict) else str(response)
        logger.log_error(f"❌ 下单失败 - 错误信息: {error_msg}，原始响应: {response}")
        return {"error": True, "reason": error_msg, "retryable": retry, "raw": response}


def close_position_with_retry(platform, symbol: str, positionSide: str, *, rate: Optional[float] = None, qty_base: Optional[float] = None, max_tries: int = 3):
    positionSide = (positionSide or "").upper()
    if rate is None and qty_base is None:
        return {"error": True, "reason": "missing_close_param"}

    BASE, CAP = 0.8, 5.0
    for attempt in range(1, max_tries + 1):
        try:
            if rate is not None:
                logger.log_info(f"🛰️ 平仓尝试 {attempt}/{max_tries}: {symbol} {positionSide} rate={rate:.6f}")
                resp = platform.close_position_by_rate(rate) if hasattr(platform, "close_position_by_rate") else platform.close_position(symbol, position_id="", qty_base=0)
            else:
                logger.log_info(f"🛰️ 平仓尝试 {attempt}/{max_tries}: {symbol} {positionSide} qty_base={qty_base}")
                resp = platform.close_position_by_base(qty_base) if hasattr(platform, "close_position_by_base") else platform.close_position(symbol, position_id="", qty_base=qty_base)
        except Exception as e:
            retry, reason = _is_retryable(None, e)
            if retry and attempt < max_tries:
                delay = min(BASE * (2 ** (attempt - 1)) + random.uniform(0, BASE), CAP)
                logger.log_error(f"⏳ 平仓失败（异常，可重试）：{e} → {delay:.2f}s 后重试")
                time.sleep(delay)
                continue
            logger.log_error(f"❌ 平仓失败（异常，放弃）：{e}")
            return {"error": True, "reason": str(e), "retryable": retry}

        if isinstance(resp, dict) and not resp.get("error"):
            logger.log_info(f"✅ 平仓请求已提交（{positionSide}）：{resp}")
            return resp

        retry, reason = _is_retryable(resp, None)
        if retry and attempt < max_tries:
            delay = min(BASE * (2 ** (attempt - 1)) + random.uniform(0, BASE), CAP)
            logger.log_error(f"⏳ 平仓失败（可重试）：原因={reason} → {delay:.2f}s 后重试；原始响应: {resp}")
            time.sleep(delay)
            continue

        error_msg = resp.get("msg", "未知错误") if isinstance(resp, dict) else str(resp)
        logger.log_error(f"❌ 平仓失败 - 错误信息: {error_msg}，原始响应: {resp}")
        return {"error": True, "reason": error_msg, "retryable": retry, "raw": resp}
# 适配锁仓/解锁业务的下单与平仓接口
def call_place_order(symbol, side, positionSide, quantity, order_type, api_key, api_secret):
    # 你可根据实际平台实现
    # TODO: 实现真实的下单逻辑
    logger.log_info(f"下单: {symbol} {side} {positionSide} {quantity} {order_type}")
    raise NotImplementedError("需要实现真实的下单API")

def call_close_position(symbol, positionSide, qty_base, api_key, api_secret):
    """平仓 - 需要实现真实的交易所API调用"""
    # TODO: 实现真实的平仓逻辑
    logger.log_info(f"平仓: {symbol} {positionSide} {qty_base}")
    raise NotImplementedError("需要实现真实的平仓API")
# core/services/order_service.py
# 功能：订单服务，负责生成和执行订单
from core.platform.base import ExchangeIf
from core.logger import logger
from core.strategy.base import StrategyBase

def build_order(strategy: StrategyBase, plan: dict) -> dict:
    """
    根据策略实例和交易计划生成订单请求
    """
    
    # 从策略实例中获取必要的信息
    symbol = plan["symbol"] if "symbol" in plan else strategy.config.get("symbol", "OPUSDT")
    qty = plan["qty"] if "qty" in plan else strategy.config.get("quantity", 1)
    price = plan["price"] if "price" in plan else strategy.config.get("price", 5000)
    side = plan["side"] if "side" in plan else "buy"
    order_type = plan["order_type"] if "order_type" in plan else "MARKET"

    order_req = {
        "symbol": symbol,
        "quantity": qty,
        "price": price,
        "side": side,
        "order_type": order_type,
        "timestamp": plan.get("timestamp", 0)  # 时间戳可以在计划中传入
    }
    
    logger.log_info(f"构建订单请求: {order_req}")
    return order_req

def place_order(platform: ExchangeIf, order_req: dict, max_tries: int = 3) -> dict:
    """
    执行下单操作：将上层的 dict order_req 映射到统一的 place_order_with_retry。
    返回平台的响应字典（或者错误字典）。
    """
    # 映射必要字段
    symbol = (order_req.get("symbol") or order_req.get("instrument") or "")
    side = (order_req.get("side") or order_req.get("direction") or "BUY")
    # positionSide 意味着 long/short；尝试从 order_req 中读取
    raw_pos = order_req.get("positionSide") or order_req.get("position_side") or order_req.get("direction") or side
    try:
        # accept enum or string
        if isinstance(raw_pos, Direction):
            position_side = raw_pos.value
        else:
            position_side = str(raw_pos).lower()
    except Exception:
        position_side = str(raw_pos).lower()
    qty = order_req.get("quantity") or order_req.get("qty") or order_req.get("quantity") or 0
    try:
        qty = float(qty)
    except Exception:
        qty = 0.0
    order_type = order_req.get("order_type") or order_req.get("type") or "MARKET"

    try:
        resp = place_order_with_retry(platform, symbol or "", side, position_side, qty, order_type, max_tries)
        logger.log_info(f"下单返回: {resp}")
        # 如果下单返回包含 orderId，则尝试确认成交
        try:
            if isinstance(resp, dict) and resp.get("orderId"):
                oid = resp.get("orderId")
                try:
                    ok, filled, avg = confirm_filled(platform, symbol or "", position_side, float(qty), hint_order_id=oid)
                except Exception as e:
                    logger.log_warning(f"确认下单状态失败: {e}")
                    ok, filled, avg = False, 0.0, None
                resp.setdefault("_confirm", {"ok": ok, "filled": filled, "avg_price": avg})
                # 若确认成交，请将成交信息写入 state（幂等且兼容部分成交）
                try:
                    if ok and (filled and float(filled) > 0):
                        try:
                            sm = StateManager()
                            state = sm.get_state()
                        except Exception:
                            sm = None
                            state = None
                        # 规范方向名称：支持 'long'/'short' 或 'buy'/'sell'
                        dnorm = str(position_side or "").lower()
                        if dnorm in ("buy", "sell"):
                            dnorm = "long" if dnorm == "buy" else "short"
                        if sm and state and dnorm in ("long", "short"):
                            try:
                                cur_pos = getattr(state, dnorm)
                                _cur_qty = float(getattr(cur_pos, "qty", 0) or 0)
                                _cur_avg = float(getattr(cur_pos, "avg_price", 0) or 0)
                                _filled = float(filled or 0)
                                _avg_px = float(avg) if (avg is not None) else None
                                # 计算新的 qty 与加权均价（若当前qty为0则直接用成交价）
                                new_qty = _cur_qty + _filled
                                if _filled > 0:
                                    if _cur_qty and _cur_avg and _avg_px:
                                        new_avg = (_cur_avg * _cur_qty + _avg_px * _filled) / new_qty
                                    else:
                                        new_avg = _avg_px or _cur_avg
                                else:
                                    new_avg = _cur_avg
                                import time
                                now_ts = int(time.time())
                                upd = {
                                    dnorm: {
                                        "qty": new_qty,
                                        "avg_price": new_avg,
                                        "last_qty": _filled,
                                        "last_fill_price": (_avg_px if _avg_px is not None else getattr(cur_pos, "last_fill_price", 0)),
                                        "last_fill_ts": now_ts
                                    }
                                }
                                sm.update_state_bulk(upd)
                                logger.log_info(f"[DEBUG] persist confirmed fill -> {upd}")
                            except Exception as e:
                                logger.log_warning(f"写入 state 失败: {e}")
                except Exception:
                    # 不应阻塞下单返回，任何写 state 的错误都只是警告
                    pass
        except Exception:
            pass
        return resp or {"error": True, "reason": "empty_response"}
    except Exception as e:
        logger.log_exception(f"下单封装失败: {e}")
        return {"error": True, "reason": str(e)}
