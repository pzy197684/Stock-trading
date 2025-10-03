# core/platform/binance.py
from urllib.parse import urlencode
import time
import hmac
import hashlib
import requests
from core.platform.base import ExchangeIf, create_error_response, create_success_response
from core.domain.enums import Direction, PositionField, ResponseField
from core.logger import logger

_BASE_MAINNET = "https://fapi.binance.com"
_BASE_TESTNET = "https://testnet.binancefuture.com"


class BinanceExchange(ExchangeIf):
    
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        super().__init__(api_key, api_secret, **kwargs)
        # 检查是否是测试网络环境
        self.is_testnet = kwargs.get('testnet', False)
        self.base_url = _BASE_TESTNET if self.is_testnet else _BASE_MAINNET
        logger.log_info(f"BinanceExchange initialized: testnet={self.is_testnet}, base_url={self.base_url}")
    
    def name(self) -> str:
        return "Binance" + (" Testnet" if self.is_testnet else "")

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

    def get_balance(self) -> dict:
        """获取账户余额"""
        account_info = self.get_account_info()
        if account_info.get("error"):
            return account_info  # 返回错误信息
        
        # 从账户信息中提取余额
        if account_info.get("success") and account_info.get("data"):
            data = account_info["data"]
            return {
                "balance": data.get("balance", 0),
                "available_balance": data.get("available_balance", 0),
            }
        else:
            return {"error": True, "reason": "Failed to get account info"}

    def place_order(self, order_req: dict) -> dict:
        """下单 - 实盘环境必须提供正确的API凭证"""
        if not self.api_key or not self.api_secret:
            raise ValueError("[BinanceExchange] API凭证未配置，无法进行实盘交易")
        
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
            direction = order_req.get("direction")
            params["side"] = direction
            # 为双向持仓模式添加 positionSide 参数
            if direction == "BUY":
                params["positionSide"] = "LONG"
            elif direction == "SELL":
                params["positionSide"] = "SHORT"
        elif order_req.get("side"):
            side = order_req.get("side")
            params["side"] = side
            # 为双向持仓模式添加 positionSide 参数
            if side == "BUY":
                params["positionSide"] = "LONG"
            elif side == "SELL":
                params["positionSide"] = "SHORT"
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

    def _get_server_time(self):
        """获取Binance服务器时间，用于避免时间同步问题"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                return response.json()['serverTime']
        except Exception as e:
            logger.log_warning(f"[BinanceExchange] Failed to get server time: {e}")
        # 如果获取服务器时间失败，fallback到本地时间
        return int(time.time() * 1000)

    def _build_signed_url_headers(self, path: str, params: dict | None = None, content_type: str | None = None):
        """Construct signed URL and headers for a given path and params.

        Returns (url, headers). This helper centralizes timestamp/signing logic for easier testing.
        """
        params = dict(params or {})
        # 使用服务器时间而不是本地时间，避免时间同步问题
        params.setdefault("timestamp", self._get_server_time())
        qs = urlencode(params, doseq=True)
        sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        url = f"{self.base_url}{path}?{qs}&signature={sig}"
        headers = {"X-MBX-APIKEY": self.api_key}
        if content_type:
            headers["Content-Type"] = content_type
        return url, headers

    def get_account_info(self) -> dict:
        """获取账户信息"""
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] get_account_info called without api credentials")
            return create_error_response("No API credentials provided")
        
        res = self._signed_get("/fapi/v2/account")
        if isinstance(res, dict):
            if res.get("error"):
                return res  # Already an error response
            elif res.get("totalWalletBalance") is not None:
                return create_success_response({
                    "balance": float(res.get("totalWalletBalance", 0)),
                    "available_balance": float(res.get("availableBalance", 0)),
                    "raw": res
                })
            else:
                return create_error_response("Invalid account info response", raw=res)
        else:
            return create_error_response("Invalid response type", raw=res)

    def get_position(self, symbol: str) -> dict:
        """获取单个交易对的持仓信息"""
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] get_position called without api credentials")
            return create_error_response("No API credentials provided")
        
        params = {"symbol": symbol}
        res = self._signed_get("/fapi/v2/positionRisk", params)
        if isinstance(res, list):
            for position in res:
                if position.get("symbol") == symbol:
                    try:
                        position_amt = float(position.get("positionAmt", 0) or 0)
                        entry_price = float(position.get("entryPrice", 0) or 0)
                        return create_success_response({
                            "symbol": symbol,
                            "size": abs(position_amt),
                            "side": "long" if position_amt > 0 else "short" if position_amt < 0 else "none",
                            "entry_price": entry_price,
                            "raw": position
                        })
                    except (ValueError, TypeError):
                        return create_error_response("Invalid position data", raw=position)
            return create_success_response({
                "symbol": symbol,
                "size": 0,
                "side": "none",
                "entry_price": 0
            })
        elif isinstance(res, dict) and res.get("error"):
            return res  # Already an error response
        else:
            return create_error_response("Invalid response type", raw=res)

    def set_leverage(self, symbol: str, leverage: int) -> dict:
        """设置交易对的杠杆倍数"""
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] set_leverage called without api credentials")
            return create_error_response("No API credentials provided")
        
        if leverage < 1 or leverage > 125:
            return create_error_response(f"Invalid leverage value: {leverage}, must be between 1 and 125")
        
        params = {
            "symbol": symbol,
            "leverage": leverage
        }
        
        res = self._signed_post("/fapi/v1/leverage", params)
        if isinstance(res, dict):
            if res.get("error"):
                return res  # Already an error response
            elif "leverage" in res and "symbol" in res:
                logger.log_info(f"✅ Binance杠杆设置成功: {symbol} -> {leverage}x")
                return create_success_response({
                    "symbol": res.get("symbol"),
                    "leverage": int(res.get("leverage")),
                    "maxNotionalValue": res.get("maxNotionalValue"),
                    "raw": res
                })
            else:
                return create_error_response("Invalid leverage response", raw=res)
        else:
            return create_error_response("Invalid response type", raw=res)

    def get_market_price(self, symbol: str) -> dict:
        """获取市场最新价格"""
        # 使用公开接口获取ticker价格，不需要签名
        url = f"{self.base_url}/fapi/v1/ticker/price"
        params = {"symbol": symbol}
        
        try:
            r = requests.get(url, params=params, timeout=(3.05, 10))
            if not r.ok:
                text = getattr(r, "text", "")
                logger.log_warning(f"[BinanceExchange] GET ticker/price returned {r.status_code}: {text}")
                return create_error_response(f"http {r.status_code}", raw=text)
            
            try:
                data = r.json()
                if "price" in data:
                    return create_success_response({
                        "symbol": data.get("symbol", symbol),
                        "price": float(data["price"]),
                        "timestamp": int(time.time() * 1000)
                    })
                else:
                    return create_error_response("Invalid ticker response", raw=data)
            except (ValueError, TypeError) as e:
                return create_error_response("Invalid price data", raw=str(e))
                
        except Exception as e:
            logger.log_error(f"[BinanceExchange] get_market_price error: {e}")
            return create_error_response("Network error", raw=str(e))

    def get_leverage(self, symbol: str) -> dict:
        """获取交易对的当前杠杆倍数"""
        if not self.api_key or not self.api_secret:
            logger.log_warning("[BinanceExchange] get_leverage called without api credentials")
            return create_error_response("No API credentials provided")
        
        params = {"symbol": symbol}
        res = self._signed_get("/fapi/v2/positionRisk", params)
        
        if isinstance(res, list):
            for position in res:
                if position.get("symbol") == symbol:
                    try:
                        leverage = int(float(position.get("leverage", 1)))
                        return create_success_response({
                            "symbol": symbol,
                            "leverage": leverage,
                            "raw": position
                        })
                    except (ValueError, TypeError):
                        return create_error_response("Invalid leverage data", raw=position)
            return create_error_response(f"Symbol {symbol} not found")
        elif isinstance(res, dict) and res.get("error"):
            return res  # Already an error response
        else:
            return create_error_response("Invalid response type", raw=res)
