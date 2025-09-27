# core/services/tp_sl_service.py
# 功能：计算止盈止损价格
def calculate_take_profit(entry_price: float, tp_percentage: float) -> float:
    """计算止盈价"""
    return entry_price * (1 + tp_percentage)

def calculate_stop_loss(entry_price: float, sl_percentage: float) -> float:
    """计算止损价"""
    return entry_price * (1 - sl_percentage)
