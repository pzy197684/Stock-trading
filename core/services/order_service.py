# core/services/order_service.py
from core.platform.base import ExchangeIf
from core.logger import logger
from core.strategy.base import StrategyBase

def build_order(strategy: StrategyBase, plan: dict) -> dict:
    """
    根据策略实例和交易计划生成订单请求
    """
    
    # 从策略实例中获取必要的信息
    symbol = plan["symbol"] if "symbol" in plan else strategy.config.get("symbol", "ETHUSDT")
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

def place_order(platform: ExchangeIf, order_req: dict) -> dict:
    """
    执行下单操作
    """
    try:
        # 调用平台 API 执行下单
        order_response = platform.place_order(order_req)
        logger.log_info(f"订单已成功下单：{order_response}")
        return order_response
    except Exception as e:
        logger.log_exception(f"下单失败: {str(e)}")
        return {"status": "error", "message": str(e)}
