# core/platform/binance.py
from urllib.parse import urlencode
import time
import hmac
import hashlib
import requests
from core.platform.base import ExchangeIf, create_error_response, create_success_response
from core.domain.enums import PositionField
from core.logger import logger

_BASE = "https://fapi.binance.com"


class BinanceExchange(ExchangeIf):
    def name(self) -> str:
        return "Binance"

    def capabilities(self) -> dict:
        return {
            "hedge_mode": True,
            "qty_unit_coin": True,
            "min_qty": 0.001,
            "qty_step": 0.001,
        }

    def _signed_get(self, path: str, params: dict | None = None):
        url, headers = self._build_signed_url_headers(path, params)
        # simple retry
        attempts = 2
        for attempt in range(1, attempts + 1):
            try:
                r = requests.get(url, headers=headers, timeout=(3.05, 10))
                if not r.ok:
                    text = getattr(r, "text", "")
                    logger.log_warning(f"[BinanceExchange] GET {path} returned {r.status_code}: {text}")
                    # return standardized error dict
                    return {"error": True, "reason": f"http {r.status_code}", "raw": text}
                try:
                    return r.json()
                except Exception:
                    return {"error": True, "reason": "invalid_json", "raw": getattr(r, "text", "")}
            except requests.exceptions.RequestException as e:
                logger.log_warning(f"[BinanceExchange] GET {path} request exception: {e}")
                if attempt < attempts:
                    time.sleep(0.5 * attempt)
                    continue
                return {"error": True, "reason": str(e), "raw": None}

    def _signed_post(self, path: str, params: dict | None = None):
        url, headers = self._build_signed_url_headers(path, params, content_type="application/x-www-form-urlencoded")
        attempts = 2
        for attempt in range(1, attempts + 1):
            try:
                r = requests.post(url, headers=headers, timeout=(3.05, 10))
                if not r.ok:
                    text = getattr(r, "text", "")
                    logger.log_warning(f"[BinanceExchange] POST {path} returned {r.status_code}: {text}")
                    return {"error": True, "reason": f"http {r.status_code}", "raw": text}
                try:
                    return r.json()
                except Exception:
                    return {"error": True, "reason": "invalid_json", "raw": getattr(r, "text", "")}
            except requests.exceptions.RequestException as e:
                logger.log_warning(f"[BinanceExchange] POST {path} request exception: {e}")
                if attempt < attempts:
                    time.sleep(0.5 * attempt)
                    continue
                return {"error": True, "reason": str(e), "raw": None}

    def _signed_delete(self, path: str, params: dict | None = None):
        url, headers = self._build_signed_url_headers(path, params)
        attempts = 2
        for attempt in range(1, attempts + 1):
            try:
                r = requests.delete(url, headers=headers, timeout=(3.05, 10))
                if not r.ok:
                    text = getattr(r, "text", "")
                    logger.log_warning(f"[BinanceExchange] DELETE {path} returned {r.status_code}: {text}")
                    return {"error": True, "reason": f"http {r.status_code}", "raw": text}
                try:
                    return r.json()
                except Exception:
                    return {"error": True, "reason": "invalid_json", "raw": getattr(r, "text", "")}
            except requests.exceptions.RequestException as e:
                logger.log_warning(f"[BinanceExchange] DELETE {path} request exception: {e}")
                if attempt < attempts:
                    time.sleep(0.5 * attempt)
                    continue
                return {"error": True, "reason": str(e), "raw": None}

    def get_order(self, symbol: str, order_id: str) -> dict:
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] get_order called without api credentials")
            return {"error": True, "reason": "no_api_key", "raw": None}
        params = {"symbol": symbol}
        if order_id:
            try:
                params["orderId"] = str(int(order_id))
            except Exception:
                params["orderId"] = str(order_id)
        res = self._signed_get("/fapi/v1/order", params)
        # normalize success shape
        if isinstance(res, dict):
            if res.get("orderId"):
                return create_success_response(res)
            elif res.get("error"):
                return res  # Already an error response
            else:
                return create_error_response("Order not found or invalid response", raw=res)
        else:
            return create_error_response("Invalid response type", raw=res)

    def get_user_trades(self, symbol: str, order_id: str | None = None, since: int | None = None, limit: int | None = None) -> dict:
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] get_user_trades called without api credentials")
            return create_error_response("No API credentials provided")
        params = {"symbol": symbol}
        if order_id is not None:
            try:
                params["orderId"] = str(int(order_id))
            except Exception:
                params["orderId"] = str(order_id)
        if since is not None:
            params["startTime"] = str(since)
        if limit is not None:
            params["limit"] = str(limit)
            
        res = self._signed_get("/fapi/v1/userTrades", params)
        # Check if API call was successful and return standardized format
        if isinstance(res, list):
            return create_success_response({"trades": res})
        elif isinstance(res, dict) and not res.get("error"):
            return create_success_response({"trades": [res]})
        else:
            return res if isinstance(res, dict) and res.get("error") else create_error_response("Failed to get user trades", raw=res)

    def get_positions(self, symbol: str) -> dict:
        # Use positionRisk endpoint as fallback to get positionAmt
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] get_positions called without api credentials")
            return {"long": {"qty": 0, "avg_price": 0}, "short": {"qty": 0, "avg_price": 0}}
        params = {"symbol": symbol}
        res = self._signed_get("/fapi/v2/positionRisk", params)
        if isinstance(res, list):
            long_p = {"qty": 0, "avg_price": 0}
            short_p = {"qty": 0, "avg_price": 0}
            for it in res:
                try:
                    amt = float(it.get("positionAmt", 0) or 0)
                except Exception:
                    amt = 0.0
                if amt > 0:
                    long_p = {"qty": abs(amt), "avg_price": float(it.get("entryPrice") or 0)}
                elif amt < 0:
                    short_p = {"qty": abs(amt), "avg_price": float(it.get("entryPrice") or 0)}
            return {"long": long_p, "short": short_p}
        return {"long": {"qty": 0, "avg_price": 0}, "short": {"qty": 0, "avg_price": 0}}

    def place_order(self, order_req: dict) -> dict:
        # Placeholder: the framework uses platform.place_order in order_service; for safety keep mock behaviour unless keys provided
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] place_order called without api credentials; returning mock response")
            return {"orderId": "mock_binance_1", "status": "NEW", "req": order_req}
        # Real implementation: POST to /fapi/v1/order with form-encoded body
        params = {}
        # map common fields
        if order_req.get("symbol"):
            params["symbol"] = order_req.get("symbol")
        elif order_req.get("instrument"):
            params["symbol"] = order_req.get("instrument")
        if order_req.get("quantity") is not None:
            params["quantity"] = str(order_req.get("quantity"))
        if order_req.get("type"):
            ot = str(order_req.get("type")).upper()
            if ot == "MARKET":
                params["type"] = "MARKET"
            else:
                params["type"] = "LIMIT"
                if order_req.get("price") is not None:
                    params["price"] = str(order_req.get("price"))
        if order_req.get("direction"):
            # convert direction to side if necessary
            params.setdefault("side", order_req.get("direction"))
        # default to post
        res = self._signed_post("/fapi/v1/order", params)
        if isinstance(res, dict):
            if res.get("orderId"):
                return create_success_response(res)
            elif res.get("error"):
                return res  # Already an error response
            else:
                return create_error_response("Order placement failed", raw=res)
        else:
            return create_error_response("Invalid response type", raw=res)

    def cancel_order(self, order_id: str) -> dict:
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] cancel_order called without api credentials; noop")
            return create_error_response("No API credentials provided", raw={"orderId": order_id, "status": "noop"})
        params = {"orderId": str(order_id)}
        res = self._signed_delete("/fapi/v1/order", params)
        if isinstance(res, dict):
            if res.get("orderId"):
                return create_success_response(res)
            elif res.get("error"):
                return res  # Already an error response
            else:
                return create_error_response("Unexpected response format", raw=res)
        else:
            return create_error_response("Invalid response type", raw=res)

    def to_instrument(self, symbol: str) -> str:
        # For Binance futures symbol is typically already like ETHUSDT; keep as-is
        return symbol

    def _build_signed_url_headers(self, path: str, params: dict | None = None, content_type: str | None = None):
        """Construct signed URL and headers for a given path and params.

        Returns (url, headers). This helper centralizes timestamp/signing logic for easier testing.
        """
        params = dict(params or {})
        params.setdefault("timestamp", int(time.time() * 1000))
        qs = urlencode(params, doseq=True)
        sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        url = f"{_BASE}{path}?{qs}&signature={sig}"
        headers = {"X-MBX-APIKEY": self.api_key}
        if content_type:
            headers["Content-Type"] = content_type
        return url, headers
