# core/services/hedge_service.py
from core.logger import logger

def lock_position(ctx, plan):
    """
    锁仓：根据策略判断是否需要触发锁仓
    """
    if ctx["locked"]:
        logger.log_warning(f"仓位已锁仓，无需重复锁仓")
        return {"status": "error", "message": "仓位已锁仓"}

    # 锁仓逻辑：标记为已锁仓，冻结该方向的仓位
    ctx["locked"] = True
    logger.log_info(f"仓位已锁仓，方向: {plan.side}, 数量: {plan.qty}")
    return {"status": "success", "message": "仓位已锁仓"}

def unlock_position(ctx, plan):
    """
    解锁仓位：根据策略判断是否解除锁仓
    """
    if not ctx["locked"]:
        logger.log_warning(f"仓位未锁仓，无法解锁")
        return {"status": "error", "message": "仓位未锁仓"}

    # 解锁逻辑：解除锁仓状态
    ctx["locked"] = False
    logger.log_info(f"仓位已解锁，方向: {plan.side}, 数量: {plan.qty}")
    return {"status": "success", "message": "仓位已解锁"}
