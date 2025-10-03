"""
Lightweight CoinW platform adapter ported from old/modules/coinw_adapter.py
Provides: get_instrument_info, get_price, get_positions, get_order,
          get_user_trades, place_order, cancel_order, close_position, to_instrument

This module prefers the legacy `modules.api_guard.safe_request_json` if available
and uses `core.logger` for logging.
"""
import os
import time
import hmac
import hashlib
import base64
import json
from typing import Dict, Any, Optional, Tuple

import requests

from core.logger import logger
from core.platform.base import ExchangeIf, create_error_response, create_success_response
from core.domain.enums import Direction, PositionField, OrderSide

# Try to import safe_request_json / is_ok from legacy modules if present
try:
    from modules.api_guard import safe_request_json, is_ok  # type: ignore
except Exception:
    # Fallback lightweight safe_request_json that mirrors minimal behavior
    def safe_request_json(method: str, url: str, *, headers: Optional[Dict[str, str]] = None,
                          data: Optional[str] = None, timeout: tuple = (3.05, 10)) -> Tuple[Optional[requests.Response], Dict[str, Any]]:
        try:
            resp = requests.request(method.upper(), url, headers=headers, data=data, timeout=timeout)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout, requests.exceptions.Timeout) as e:
            return None, {"code": -2, "data": [], "msg": f"timeout: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return None, {"code": -3, "data": [], "msg": f"network: {str(e)}"}
        try:
            payload = resp.json()
            if not isinstance(payload, dict):
                payload = {"code": None, "data": payload}
        except Exception as e:
            payload = {"code": -4, "data": [], "msg": f"json: {str(e)}", "status": getattr(resp, "status_code", None)}
            return resp, payload
        if not getattr(resp, "ok", False):
            if "code" not in payload:
                payload.update({"code": -5, "msg": f"http_status={getattr(resp,'status_code',None)}"})
            return resp, payload
        return resp, payload

    def is_ok(data: Any, expect: str = "list") -> bool:
        if not isinstance(data, dict):
            return False
        code = data.get("code", None)
        if code not in (0, None):
            return False
        dv = data.get("data", None)
        if expect == "list":
            return isinstance(dv, list)
        if expect == "dict":
            return isinstance(dv, dict)
        if expect == "any":
            return "data" in data
        return False

# ---- 基础配置（可用环境变量覆盖，便于灰度）----
_BASE = os.environ.get("COINW_BASE_URL", "https://api.coinw.com")
_TIMEOUT = (3.05, 10)

def _now_ms() -> int:
    return int(time.time() * 1000)

def _sign(secret: str, ts: int, method: str, path: str, query: str = "", body: str = "") -> str:
    raw = f"{ts}{method.upper()}{path}{query or body}"
    digest = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()

def _headers(api_key: str, sign: str, ts: int) -> Dict[str, str]:
    return {"api_key": api_key, "sign": sign, "timestamp": str(ts), "Content-Type": "application/json"}

def _request(api_key: str, secret: str, method: str, path: str,
             params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None):
    ts = _now_ms()
    url = _BASE + path
    query = ""
    body = ""
    if method.upper() == "GET" and params:
        from urllib.parse import urlencode
        query = "?" + urlencode(params, doseq=True)
        url += query
    elif json_body:
        body = json.dumps(json_body, separators=(",", ":"), ensure_ascii=False)
    sign = _sign(secret, ts, method, path, query=query if method.upper() == "GET" else "", body=body if method.upper() != "GET" else "")
    hdr = _headers(api_key, sign, ts)
    resp, data = safe_request_json(method=method, url=url, headers=hdr, data=(body if body else None), timeout=_TIMEOUT)
    if not (getattr(resp, "ok", True)):
        logger.log_error(f"[coinw http] {method} {path} status={getattr(resp,'status_code',None)} data={data}")
    return resp, data


# ---------- 元数据 ----------
def get_instrument_info(instrument: str, api_key: str = "", secret: str = "") -> Dict[str, Any]:
    path = "/v1/perpum/instruments"
    resp, data = _request(api_key, secret, "GET", path, params={"name": instrument})
    item = (data.get("data") or [{}])[0] if isinstance(data.get("data"), list) else (data.get("data") or {})
    return {
        "_raw": data,
        "pricePrecision": int(item.get("pricePrecision") or 2),
        "oneLotSize": float(item.get("oneLotSize") or 0.001),
        "minSize": float(item.get("minSize") or 0.001),
    }

def get_price(instrument: str) -> float:
    path = "/v1/perpumPublic/ticker"
    url = f"{_BASE}{path}?instrument={instrument}"
    _, data = safe_request_json("GET", url, timeout=_TIMEOUT)
    if not is_ok(data, expect="any"):
        logger.log_error(f"[coinw price] invalid payload: {data}")
        return 0.0
    dv = data.get("data")
    if isinstance(dv, list):
        d = dv[0] if dv else {}
    elif isinstance(dv, dict):
        d = dv
    else:
        d = {}
    lp = (d.get("last_price") or d.get("lastPrice") or d.get("last")
          or d.get("c") or d.get("close") or d.get("price"))
    try:
        return float(lp) if lp is not None else 0.0
    except Exception:
        return 0.0


# ---------- 仓位/订单 ----------
def get_positions(api_key: str, secret: str, instrument: str) -> Dict[str, Any]:
    path = "/v1/perpum/positions"
    resp, data = _request(api_key, secret, "GET", path, params={"instrument": instrument})
    long_pos, short_pos = {PositionField.QTY: 0.0, PositionField.AVG_PRICE: 0.0, "id": None}, {PositionField.QTY: 0.0, PositionField.AVG_PRICE: 0.0, "id": None}
    try:
        info = get_instrument_info(instrument)
        _lot_size = float(info.get("oneLotSize") or 0.01)
    except Exception:
        _lot_size = 0.01
    if not is_ok(data, expect="list"):
        return {"_ok": False, "long": long_pos, "short": short_pos, "_raw": (data or {"code": -1, "msg": "invalid response"})}
    for it in (data.get("data") or []):
        side = str(it.get("direction") or "").lower()
        pid = it.get("id")
        _base_size = it.get("baseSize")
        if _base_size is not None:
            try:
                qty = float(_base_size)
                _lots = float(it.get("currentPiece") or 0.0)
                if _lots > 0:
                    _inferred = qty / _lots
                    logger.log_info(f"🧪 [面值推断] {instrument} oneLotSize≈{_inferred:.6f} (=baseSize/currentPiece)")
            except Exception:
                qty = 0.0
        else:
            qty_lots = float(it.get("currentPiece") or 0.0)
            qty = qty_lots * _lot_size
        avg = float(it.get("openPrice") or 0.0)
        if side == Direction.LONG:
            long_pos.update({PositionField.QTY: qty, PositionField.AVG_PRICE: avg, "id": pid})
        elif side == Direction.SHORT:
            short_pos.update({PositionField.QTY: qty, PositionField.AVG_PRICE: avg, "id": pid})
    return {"_ok": True, "long": long_pos, "short": short_pos, "_raw": data}

def get_order(api_key: str, secret: str, instrument: str, order_id: str = "", client_id: str = "") -> Dict[str, Any]:
    path = "/v1/perpum/orders/one"
    params = {"instrument": instrument}
    if order_id: params["orderId"] = order_id
    if client_id: params["thirdOrderId"] = client_id
    _, data = _request(api_key, secret, "GET", path, params=params)
    if not is_ok(data, expect="dict"):
        return {
            "code": data.get("code", -1) if isinstance(data, dict) else -1,
            "data": {},
            "msg": (data.get("msg") or data.get("message") or "invalid response") if isinstance(data, dict) else "invalid response",
            "_raw": data
        }
    return data or {}

def get_user_trades(api_key: str, secret: str, instrument: str, order_id: str = "") -> Dict[str, Any]:
    path = "/v1/perpum/tradeList"
    params = {"instrument": instrument}
    if order_id:
        params["orderId"] = order_id
    _, data = _request(api_key, secret, "GET", path, params=params)
    if not is_ok(data, expect="list"):
        return {
            "code": data.get("code", -1) if isinstance(data, dict) else -1,
            "data": [],
            "msg": (data.get("msg") or data.get("message") or "invalid response") if isinstance(data, dict) else "invalid response",
            "_raw": data
        }
    return data or {}

def place_order(api_key: str, secret: str, instrument: str, direction: str,
                qty: float, order_type: str = "MARKET", leverage: int = 100,
                client_id: str = "", quantityUnit: int = 2, price: Optional[float] = None) -> Dict[str, Any]:
    path = "/v1/perpum/order"
    if qty is None or float(qty) <= 0:
        return {"error": True, "reason": "qty_normalize_failed", "orig_qty": qty}
    _position_model = 1
    body: Dict[str, Any] = {
        "instrument": instrument,
        "direction": direction,
        "quantityUnit": 2,
        "quantity": float(qty),
        "leverage": leverage,
        "positionModel": _position_model,
        "positionType": "execute",
    }
    if client_id:
        body["thirdOrderId"] = client_id
    if order_type and order_type.upper() != "MARKET":
        body["type"] = "limit"
        if price is not None:
            body["price"] = price
    resp, data = _request(api_key, secret, "POST", path, json_body=body)
    if isinstance(data, dict) and data.get("code") == 0:
        d = data.get("data")
        oid = None
        if isinstance(d, dict):
            oid = d.get("orderId") or d.get("value")
        if not oid:
            oid = data.get("orderId")
        if oid:
            return {"orderId": str(oid), "status": "NEW"}
    return data or {}

def cancel_order(api_key: str, secret: str, instrument: str, order_id: str = "", client_id: str = "") -> Dict[str, Any]:
    path = "/v1/perpum/order"
    params = {"instrument": instrument}
    if order_id: params["orderId"] = order_id
    if client_id: params["thirdOrderId"] = client_id
    resp, data = _request(api_key, secret, "DELETE", path, params=params)
    return data or {}

def close_position(
    api_key: str, secret: str, position_id: str,
    closeNum: Optional[float] = None, closeRate: Optional[float] = None,
    qty_base: Optional[float] = None, instrument: Optional[str] = None
) -> Dict[str, Any]:
    path = "/v1/perpum/positions"
    body: Dict[str, Any] = {"id": position_id}
    if isinstance(closeRate, (int, float)) and closeRate > 0:
        body["closeRate"] = min(float(closeRate), 1.0)
    elif isinstance(closeNum, (int, float)) and closeNum > 0:
        body["closeNum"] = float(closeNum)
    elif isinstance(qty_base, (int, float)) and qty_base > 0:
        try:
            lot_size = 0.01
            if instrument:
                info = get_instrument_info(instrument)
                lot_size = float(info.get("oneLotSize") or lot_size)
            pos = get_positions(api_key, secret, instrument or "")
            lots_total = 0.0
            for side in ("long", "short"):
                it = (pos.get(side) or {})
                if str(it.get("id") or "") == str(position_id):
                    qty_base_total = float(it.get(PositionField.QTY) or 0.0)
                    lots_total = (qty_base_total / lot_size) if lot_size > 0 else 0.0
                    break
            if lots_total > 0 and lot_size > 0:
                rate = float(qty_base) / float(lots_total * lot_size)
                if rate >= 1.0:
                    body["closeRate"] = 1.0
                elif rate > 0:
                    body["closeRate"] = rate
                else:
                    import math
                    body["closeNum"] = max(1.0, math.floor(float(qty_base) / lot_size))
        except Exception:
            body.setdefault("closeNum", 1.0)
    else:
        return {"error": True, "reason": "missing closeRate/closeNum/qty_base"}
    resp, data = _request(api_key, secret, "DELETE", path, json_body=body)
    return data or {}

def to_instrument(symbol: str) -> str:
    return symbol[:-4] if symbol.endswith("USDT") else symbol


class CoinWExchange(ExchangeIf):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret)

    def name(self) -> str:
        return "CoinW"

    def capabilities(self) -> dict:
        return {
            "hedge_mode": False,
            "qty_unit_coin": True,
            "min_qty": 0.01,
            "qty_step": 0.01,
        }

    def get_position(self, symbol: str) -> dict:
        # delegate to module-level get_positions
        inst = to_instrument(symbol)
        res = get_positions(self.api_key, self.api_secret, inst)
        # module returns {_ok: bool, long: {...}, short: {...}, _raw: ...}
        if isinstance(res, dict):
            return res
        return {"error": True, "reason": "invalid_response", "raw": res}

    def get_positions(self, symbol: str) -> dict:
        inst = to_instrument(symbol)
        res = get_positions(self.api_key, self.api_secret, inst)
        if isinstance(res, dict):
            return res
        return {"error": True, "reason": "invalid_response", "raw": res}

    def get_order(self, symbol: str, order_id: str = "") -> dict:
        inst = to_instrument(symbol)
        res = get_order(self.api_key, self.api_secret, inst, order_id=order_id)
        # normalize: expect dict possibly containing data or orderId
        if not isinstance(res, dict):
            return {"error": True, "reason": "invalid_response", "raw": res}
        # coinw may return wrapped structure
        if res.get("orderId"):
            return res
        d = res.get("data") or res.get("data", {})
        if isinstance(d, dict) and (d.get("orderId") or d.get("value") or d.get("id")):
            oid = d.get("orderId") or d.get("value") or d.get("id")
            return {"orderId": str(oid), "status": d.get("status") or res.get("status") or "UNKNOWN", "req": d}
        # fallback: if code exists, return error dict
        if res.get("code") not in (0, None):
            return {"error": True, "reason": res.get("msg") or "api_error", "raw": res}
        return res

    def get_user_trades(self, symbol: str, order_id: str | None = None) -> dict:
        inst = to_instrument(symbol)
        res = get_user_trades(self.api_key, self.api_secret, inst, order_id=order_id or "")
        if not isinstance(res, dict):
            return create_error_response("invalid_response", raw=res)
        # expect {'code':0,'data':[...]} or similar
        if res.get("code") not in (0, None):
            return create_error_response(res.get("msg") or "api_error", code=str(res.get("code")), raw=res)
        
        # Return standardized format with trades list
        trades_data = res.get("data") if isinstance(res.get("data"), list) else []
        return create_success_response({"trades": trades_data})

    def place_order(self, order_req: dict) -> dict:
        # adapt dict-based order_req to module-level place_order signature
        inst = order_req.get("instrument") or to_instrument(order_req.get("symbol", ""))
        direction = order_req.get("direction") or order_req.get("side") or Direction.LONG
        qty = order_req.get("quantity") or order_req.get(PositionField.QTY) or order_req.get("quantity") or 0.0
        otype = order_req.get("type") or order_req.get("order_type") or "MARKET"
        client_id = order_req.get("thirdOrderId") or order_req.get("client_id") or ""
        price = order_req.get("price")
        # coerce qty to float
        try:
            qty_f = float(qty)
        except Exception:
            qty_f = 0.0
        res = place_order(self.api_key, self.api_secret, inst, direction, qty_f, order_type=otype, client_id=client_id, price=price)
        if isinstance(res, dict) and res.get("orderId"):
            return res
        # normalize coinw success shape
        if isinstance(res, dict) and res.get("code") in (0, None):
            data = res.get("data")
            if isinstance(data, dict):
                oid = data.get("orderId") or data.get("value") or res.get("orderId")
                if oid:
                    return {"orderId": str(oid), "status": "NEW", "req": order_req}
        return {"error": True, "reason": "place_failed", "raw": res}

    def cancel_order(self, order_id: str) -> dict:
        # coinw cancel supports instrument + orderId or thirdOrderId; here we only pass order_id
        res = cancel_order(self.api_key, self.api_secret, "", order_id=order_id)
        if isinstance(res, dict) and (res.get("orderId") or res.get("code") in (0, None)):
            return res
        return {"error": True, "reason": "cancel_failed", "raw": res}
