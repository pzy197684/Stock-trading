# core/config_live.py
# 功能：运行期配置热加载，仅合并白名单字段，打印变更日志
import os
import json
from copy import deepcopy
from decimal import Decimal
from core.logger import logger

# 允许热更的字段白名单（点号路径）
_WHITELIST = {
    "order_type",
    "interval",
    "long.first_qty", "long.add_ratio", "long.max_add_times", "long.add_interval",
    "long.tp_first_order", "long.tp_before_full", "long.tp_after_full",
    "short.first_qty", "short.add_ratio", "short.max_add_times", "short.add_interval",
    "short.tp_first_order", "short.tp_before_full", "short.tp_after_full",
    "hedge.min_wait_seconds", "hedge.trigger_loss",
    "hedge.release_tp_after_full.long", "hedge.release_tp_after_full.short",
    "hedge.release_sl_loss_ratio.long", "hedge.release_sl_loss_ratio.short",
    "risk_control.cooldown_minutes",
    "risk_control.max_total_qty",
    "risk_control.tp_slippage",
    "risk_control.fast_add_window_minutes",
    "risk_control.fast_add_pause_minutes",
}

_LAST = {
    "path": None,
    "mtime": 0.0,
}

def _get(d: dict, path: str):
    node = d
    for k in path.split("."):
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node

def _set(d: dict, path: str, value):
    node = d
    keys = path.split(".")
    for k in keys[:-1]:
        if not isinstance(node, dict):
            return  # 遇到 None 或非 dict，直接跳过
        if k not in node or not isinstance(node[k], dict):
            node[k] = {}
        node = node[k]
    if isinstance(node, dict):
        node[keys[-1]] = value

def _fmt(v):
    if isinstance(v, Decimal):
        return float(v)
    return v

def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _diff_and_apply(cfg: dict, new_cfg: dict, base: dict = {}):
    if not isinstance(cfg, dict) or not isinstance(new_cfg, dict):
        return False, []
    changed = False
    changes = []
    base_d = cfg if base is None else base
    for key in sorted(_WHITELIST):
        nv = _get(new_cfg, key)
        if nv is None:
            continue
        if not isinstance(base_d, dict):
            continue
        ov = _get(base_d, key)
        if _fmt(ov) != _fmt(nv):
            _set(cfg, key, nv)
            changes.append(f"{key}: {ov} → {nv}")
            changed = True
    return changed, changes

def reload_if_changed(cfg: dict, default_path: str):
    if not isinstance(cfg, dict):
        return cfg
    path = cfg.get("_config_path") or default_path
    if not path or not os.path.isfile(path):
        return cfg
    try:
        mtime = os.path.getmtime(path)
    except Exception as e:
        logger.log_warning(f"⚠️ [热加载] 读取配置文件时间失败：{e}")
        return cfg
    if _LAST["path"] == path and _LAST["mtime"] == mtime:
        return cfg
    try:
        fresh = _load_json(path)
    except Exception as e:
        logger.log_warning(f"⚠️ [热加载] 配置解析失败，忽略此次更新：{e}")
        return cfg
    old_cfg_snapshot = deepcopy(cfg)
    changed, changes = _diff_and_apply(cfg, fresh, base=old_cfg_snapshot)
    _LAST["path"] = path
    _LAST["mtime"] = mtime
    if changed and changes:
        logger.log_info("🧪 [热加载] 检测到配置变更（仅白名单字段已合并，下一轮生效）：")
        for line in changes:
            logger.log_info(f"   • {line}")
    else:
        from copy import deepcopy as _dc
        _old = _dc(old_cfg_snapshot)
        _ov = _get(_old, "long.tp_after_full")
        _nv = _get(fresh, "long.tp_after_full")
        logger.log_info(f"🧪 [热加载] 检测到配置文件更新时间，但白名单字段无变化。diag long.tp_after_full: old={_ov} new={_nv}")
    return cfg
