# core/services/trader.py
# 适配锁仓/解锁业务的行情与持仓接口
from core.logger import logger

def get_price(symbol):
    # 你可根据实际平台实现
    logger.log_info(f"[MOCK] 获取市价: {symbol}")
    return 100.0

def get_position(api_key, api_secret, symbol):
    # 你可根据实际平台实现
    logger.log_info(f"[MOCK] 获取持仓: {symbol}")
    return {
        "long": {"qty": 1.0, "avg_price": 100.0},
        "short": {"qty": 1.0, "avg_price": 100.0}
    }
