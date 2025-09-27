# 解锁执行模块
from decimal import Decimal, getcontext
getcontext().prec = 18

from core.logger import logger
from core.managers.state_manager import StateManager
from core.services.trader import get_price, get_position
from core.utils.helpers import get_pos_dict

# 你可根据需要补充 call_close_position、write_log 等依赖

def _is_ok_resp(resp) -> bool:
    try:
        if not isinstance(resp, dict):
            return False
        if resp.get("code") == 0:
            return True
        if resp.get("ok") is True:
            return True
        if "orderId" in resp:
            return True
        data = resp.get("data") or {}
        if isinstance(data, dict) and (data.get("orderId") or data.get("value")):
            return True
    except Exception:
        pass
    return False

def _close_side(symbol, direction, qty, api_key, api_secret, order_type="MARKET"):
    positionSide = "LONG" if direction == "long" else "SHORT"
    # 你需实现 call_close_position
    from core.services.order_service import call_close_position
    resp = call_close_position(
        symbol=symbol,
        positionSide=positionSide,
        qty_base=float(qty),
        api_key=api_key,
        api_secret=api_secret
    )
    return resp

def execute_hedge_take_profit(symbol, direction, api_key, api_secret, order_type="MARKET", account=None):
    try:
        sm = StateManager(account)
        state = sm.get_state()
        opp_dir = "short" if direction == "long" else "long"
        _pd = get_pos_dict(position=None, state=state.__dict__, direction=direction)
        px = Decimal(str(get_price(symbol)))
        qty = Decimal(str(_pd.get("qty", 0)))
        avg_price = Decimal(str(_pd.get("avg_price", 0)))
        hedge_locked = bool(_pd.get("hedge_locked", False))
        if qty <= 0 or avg_price <= 0 or not hedge_locked:
            logger.log_warning(f"⚠️ 解锁止盈：{direction} 无可平仓或未处于锁仓，跳过")
            return
        pnl_per = px - avg_price if direction == "long" else avg_price - px
        realized_profit = (pnl_per * qty) if pnl_per > 0 else Decimal("0")
        logger.log_info(f"📤 解锁止盈执行：{direction} qty={qty}, avg={avg_price:.6f}, px={px:.6f}, pnl={realized_profit:.2f}")
        resp = _close_side(symbol, direction, qty, api_key, api_secret, order_type)
        if not _is_ok_resp(resp):
            logger.log_error(f"❌ 解锁止盈平仓失败：{resp}")
            return
        opp_state = getattr(state, opp_dir, None)
        prev_lp = Decimal(str(getattr(opp_state, 'locked_profit', 0) if opp_state else 0))
        new_lp  = prev_lp + (realized_profit if realized_profit > 0 else Decimal("0"))
        sm.update_state_bulk({
            direction: {
                "qty": 0,
                "avg_price": 0,
                "add_times": 0,
                "last_add_time": None,
                "hedge_locked": False,
                "hedge_stop": True
            },
            opp_dir: {
                "hedge_locked": True,
                "hedge_stop": True,
                "locked_profit": float(new_lp)
            }
        })
        try:
            real_pos = get_position(api_key, api_secret, symbol) or {}
            lq  = (real_pos.get("long")  or {}).get("qty", 0)
            la  = (real_pos.get("long")  or {}).get("avg_price", 0)
            sq  = (real_pos.get("short") or {}).get("qty", 0)
            sa  = (real_pos.get("short") or {}).get("avg_price", 0)
            sm.update_state_bulk({
                "long":  {"qty": lq, "avg_price": la, "opposite_qty": sq},
                "short": {"qty": sq, "avg_price": sa, "opposite_qty": lq}
            })
            logger.log_info(f"📊 解锁止盈后回读同步：long={lq}@{la:.4f}, short={sq}@{sa:.4f}")
        except Exception as _e:
            logger.log_warning(f"⚠️ 解锁止盈回读同步失败：{_e}")
        logger.log_info(f"🪵 解锁止盈完成：平掉 {direction}，对侧继续锁仓停机，locked_profit={float(realized_profit):.2f}")
        # CSV 日志可按需实现
    except Exception as e:
        logger.log_error(f"❌ execute_hedge_take_profit 异常：{e}")
        raise

def execute_hedge_stop_loss(symbol, direction, api_key, api_secret, order_type="MARKET", account=None):
    try:
        sm = StateManager(account)
        state = sm.get_state()
        opp_dir = "short" if direction == "long" else "long"
        _pd = get_pos_dict(position=None, state=state.__dict__, direction=direction)
        try:
            real_pos = get_position(api_key, api_secret, symbol) or {}
            lq  = (real_pos.get("long")  or {}).get("qty", 0)
            la  = (real_pos.get("long")  or {}).get("avg_price", 0)
            sq  = (real_pos.get("short") or {}).get("qty", 0)
            sa  = (real_pos.get("short") or {}).get("avg_price", 0)
            sm.update_state_bulk({
                "long":  {"qty": lq, "avg_price": la, "opposite_qty": sq},
                "short": {"qty": sq, "avg_price": sa, "opposite_qty": lq}
            })
            logger.log_info(f"📊 解锁止损后回读同步：long={lq}@{la:.4f}, short={sq}@{sa:.4f}")
        except Exception as _e:
            logger.log_warning(f"⚠️ 解锁止损回读同步失败：{_e}")
        _px_raw = get_price(symbol)
        px = Decimal(str(_px_raw if _px_raw is not None else _pd.get("avg_price", 0)))
        qty = Decimal(str(_pd.get("qty", 0)))
        avg_price = Decimal(str(_pd.get("avg_price", 0)))
        hedge_locked = bool(_pd.get("hedge_locked", False))
        if qty <= 0 or avg_price <= 0 or not hedge_locked:
            logger.log_warning(f"⚠️ 解锁止损：{direction} 无可平仓或未处于锁仓，跳过")
            return
        loss_per = avg_price - px if direction == "long" else px - avg_price
        loss_amount = (loss_per * qty) if loss_per > 0 else Decimal("0")
        from core.config_loader import load_config
        _conf = load_config() or {}
        locked_profit = Decimal(str(_pd.get("locked_profit", 0)))
        hedge_conf = _conf.get("hedge", {}) if isinstance(_conf, dict) else {}
        ratio_map = hedge_conf.get("release_sl_loss_ratio", {}) if isinstance(hedge_conf, dict) else {}
        ratio = Decimal(str(ratio_map[direction] if isinstance(ratio_map, dict) and direction in ratio_map else 1.0))
        limit = locked_profit * ratio
        logger.log_info(
            f"🧮 解锁止损判断 → 方向={direction}, 浮亏金额={loss_amount:.2f}, 限制={limit:.2f} "
            f"(locked_profit={locked_profit:.2f} × ratio={ratio:.4f})"
        )
        if loss_amount <= 0:
            logger.log_info("🟢 解锁止损执行：当前已转盈利，跳过阈值检查直接平仓")
        elif loss_amount > limit:
            logger.log_info("🪵 解锁止损条件不满足（亏损仍大于限制），保持锁仓")
            return
        resp = _close_side(symbol, direction, qty, api_key, api_secret, order_type)
        if not _is_ok_resp(resp):
            logger.log_error(f"❌ 解锁止损平仓失败：{resp}")
            return
        sm.update_state_bulk({
            direction: {
                "qty": 0,
                "avg_price": 0,
                "add_times": 0,
                "last_add_time": None,
                "hedge_locked": False,
                "hedge_stop": False,
                "locked_profit": 0
            },
            opp_dir: {
                "hedge_locked": False,
                "hedge_stop": False,
                "locked_profit": 0
            }
        })
        logger.log_info("🪵 解锁止损完成：两侧锁仓/停机标志已清除，亏损侧已清仓")
        try:
            real_pos = get_position(api_key, api_secret, symbol) or {}
            lq  = (real_pos.get("long")  or {}).get("qty", 0)
            la  = (real_pos.get("long")  or {}).get("avg_price", 0)
            sq  = (real_pos.get("short") or {}).get("qty", 0)
            sa  = (real_pos.get("short") or {}).get("avg_price", 0)
            sm.update_state_bulk({
                "long":  {"qty": lq, "avg_price": la, "opposite_qty": sq},
                "short": {"qty": sq, "avg_price": sa, "opposite_qty": lq}
            })
            logger.log_info(f"📊 解锁止损后回读同步：long={lq}@{la:.4f}, short={sq}@{sa:.4f}")
        except Exception as _e:
            logger.log_warning(f"⚠️ 解锁止损回读同步失败：{_e}")
        # CSV 日志可按需实现
    except Exception as e:
        logger.log_error(f"❌ execute_hedge_stop_loss 异常：{e}")
        raise
