# -*- coding: utf-8 -*-
# 文件名：execute/risk_control.py
# 风控模块重构版

import time
from typing import List, Optional, Dict, Any, Union

from core.managers.state_manager import StateManager
from core.logger import logger
from core.domain.enums import Direction, PositionField


# ---------- 配置读取工具 ----------
def get_risk_control_config(cfg: dict) -> dict:
    return (cfg.get("risk_control") or {}) if isinstance(cfg, dict) else {}

def get_fast_add_window_sec(cfg: dict) -> int:
    return int(get_risk_control_config(cfg).get("fast_add_window_sec", 300))

def get_fast_add_pause_sec(cfg: dict) -> int:
    return int(get_risk_control_config(cfg).get("fast_add_pause_sec", 3600))


# ---------- 风控 1：连续加仓冷却 ----------
def mark_add_event(direction: str, config: dict, now: Optional[int] = None, account: Optional[str] = None) -> int:
    if direction not in (Direction.LONG, Direction.SHORT):
        return 0

    now = int(now or time.time())
    window_sec = get_fast_add_window_sec(config)
    pause_sec = get_fast_add_pause_sec(config)

    sm = StateManager(account)
    st = sm.get_state()
    node = getattr(st, direction)
    
    # 兼容 add_history 字段为 list 或不存在的情况
    hist = getattr(node, "add_history", None)
    if not isinstance(hist, list):
        hist = []
    # 追加并裁剪长度
    hist.append(now)
    hist = [int(x) for x in hist if isinstance(x, (int, float))][-5:]
    # 统计窗口内次数
    cutoff = now - window_sec
    recent = [ts for ts in hist if ts >= cutoff]
    paused_until = 0
    if len(recent) >= 2:
        paused_until = now + pause_sec
    # 写回状态
    update_dict = {direction: {"add_history": hist}}
    if paused_until:
        # 直接写入 fast_add_paused_until 字段（PositionState 已有该字段）
        update_dict[direction][PositionField.FAST_ADD_PAUSED_UNTIL] = int(paused_until) # type: ignore
    sm.update_state_bulk(update_dict)

    if paused_until:
        logger.log_info(f"⏳ 触发连续加仓冷却：{direction} 暂停加仓至 {paused_until} (epoch)")
    return int(paused_until)

def should_pause_due_to_fast_add(state, direction: str, config: dict, now: Optional[int] = None, account: Optional[str] = None) -> bool:
    # state 可为 AccountState 或 dict
    if direction not in (Direction.LONG, Direction.SHORT):
        return False

    now = int(now or time.time())
    if hasattr(state, direction):
        d = getattr(state, direction)
        until = int(getattr(d, PositionField.FAST_ADD_PAUSED_UNTIL, 0) or 0)
    elif isinstance(state, dict):
        d = state.get(direction) or {}
        until = int(d.get(PositionField.FAST_ADD_PAUSED_UNTIL, 0) or 0)
    else:
        return False
    logger.log_info(f"[PAUSE-CHK] dir={direction} now={now} until={until} left={until-now}")

    if until > now:
        return True

    # 过期清零
    if until and until <= now:
        try:
            sm = StateManager(account)
            sm.update_state_bulk({direction: {PositionField.FAST_ADD_PAUSED_UNTIL: 0}})
            logger.log_info(f"✅ 连续加仓冷却结束：{direction} 已恢复可加仓")
        except Exception:
            pass
    return False

# ---------- 风控 3：盈利提取（预留） ----------
def check_and_extract_profit(state: dict, config: dict):
    rc = get_risk_control_config(config)
    pe = (config.get("profit_extract") or {})
    if not pe or not pe.get("enabled"):
        return
    logger.log_warning("💡 盈利提取（预留）：已启用配置，但当前版本未实现具体提取逻辑。")