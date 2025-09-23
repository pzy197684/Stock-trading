# core/platform/coinw.py
from core.platform.base import ExchangeIf

class CoinWExchange(ExchangeIf):
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
        # 假设从 CoinW 获取仓位的逻辑
        return {"symbol": symbol, "qty": 50, "avg_price": 200}

    def place_order(self, order_req: dict) -> dict:
        # 模拟下单逻辑，实际应该调用 CoinW API
        return {"order_id": 789012, "status": "success", "order_details": order_req}

    def cancel_order(self, order_id: str) -> dict:
        # 模拟取消订单的逻辑
        return {"order_id": order_id, "status": "canceled"}
