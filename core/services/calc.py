# core/services/calc.py
def calculate_profit(entry_price: float, exit_price: float, qty: float) -> float:
    """计算盈利或亏损"""
    return (exit_price - entry_price) * qty

def calculate_position_value(price: float, qty: float) -> float:
    """计算仓位的总价值"""
    return price * qty
