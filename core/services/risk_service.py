# core/services/risk_service.py
from core.logger import logger

def allow_risk(ctx, plan):
    """
    判断是否符合风控条件
    """
    # 示例：检查可用仓位是否足够
    if ctx["available_capacity"] < plan["qty"]:
        logger.log_warning(f"仓位不足：当前可用仓位 {ctx['available_capacity']} 小于计划加仓量 {plan["qty"]}")
        return False, "仓位不足"
    
    # 示例：冷静期限制
    if ctx["cooldown"] > 0:
        logger.log_warning(f"冷静期限制：等待 {ctx['cooldown']} 秒后再交易")
        return False, "冷静期限制"

    # 示例：熔断条件
    if ctx["circuit_breaker"]:
        logger.log_warning(f"熔断已触发，停止交易")
        return False, "熔断触发"

    return True, ""
