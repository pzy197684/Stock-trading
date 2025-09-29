# -*- coding: utf-8 -*-
# core/strategy/martingale_hedge/utils.py
# 功能：马丁对冲策略辅助工具函数

from typing import Dict, Any, List, Optional, Tuple
from core.utils.decimal_ext import Decimal, ZERO
from core.logger import logger
import time
import json

class MartingaleStateManager:
    """
    马丁对冲策略状态管理器
    
    负责：
    1. 状态的序列化和反序列化
    2. 状态验证和修复
    3. 历史记录管理
    4. 状态迁移和升级
    """
    
    @staticmethod
    def create_default_state() -> Dict[str, Any]:
        """创建默认状态结构"""
        return {
            "long": {
                "qty": 0.0,
                "avg_price": 0.0,
                "add_times": 0,
                "last_qty": 0.0,
                "last_entry_price": 0.0,
                "last_fill_price": 0.0,
                "last_fill_ts": 0,
                "last_open_ts": 0,
                "add_history": [],
                "round": 1,
                "opposite_qty": 0.0,
                "fast_add_paused_until": 0,
                "hedge_state": {
                    "hedge_locked": False,
                    "hedge_stop": False,
                    "locked_profit": 0.0,
                    "hedge_locked_on_full": False,
                    "cooldown_until": 0
                }
            },
            "short": {
                "qty": 0.0,
                "avg_price": 0.0,
                "add_times": 0,
                "last_qty": 0.0,
                "last_entry_price": 0.0,
                "last_fill_price": 0.0,
                "last_fill_ts": 0,
                "last_open_ts": 0,
                "add_history": [],
                "round": 1,
                "opposite_qty": 0.0,
                "fast_add_paused_until": 0,
                "hedge_state": {
                    "hedge_locked": False,
                    "hedge_stop": False,
                    "locked_profit": 0.0,
                    "hedge_locked_on_full": False,
                    "cooldown_until": 0
                }
            },
            "global": {
                "exchange_fault_until": 0,
                "backfill_done": {"long": False, "short": False},
                "schema_version": "1.0.0",
                "last_update": int(time.time())
            }
        }
    
    @staticmethod
    def validate_state(state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证状态结构的完整性
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        try:
            # 检查顶层结构
            required_keys = ["long", "short", "global"]
            for key in required_keys:
                if key not in state:
                    errors.append(f"缺少顶层键: {key}")
            
            # 检查方向状态结构
            for direction in ["long", "short"]:
                if direction not in state:
                    continue
                    
                dir_state = state[direction]
                required_fields = [
                    "qty", "avg_price", "add_times", "last_qty",
                    "add_history", "hedge_state"
                ]
                
                for field in required_fields:
                    if field not in dir_state:
                        errors.append(f"缺少{direction}.{field}")
                
                # 检查锁仓状态结构
                if "hedge_state" in dir_state:
                    hedge_state = dir_state["hedge_state"]
                    hedge_fields = ["hedge_locked", "hedge_stop", "locked_profit"]
                    for field in hedge_fields:
                        if field not in hedge_state:
                            errors.append(f"缺少{direction}.hedge_state.{field}")
            
            # 数值有效性检查
            for direction in ["long", "short"]:
                if direction not in state:
                    continue
                    
                dir_state = state[direction]
                
                # 数量不能为负
                if dir_state.get("qty", 0) < 0:
                    errors.append(f"{direction}.qty 不能为负数")
                
                # 均价不能为负
                if dir_state.get("avg_price", 0) < 0:
                    errors.append(f"{direction}.avg_price 不能为负数")
                
                # 加仓次数不能为负
                if dir_state.get("add_times", 0) < 0:
                    errors.append(f"{direction}.add_times 不能为负数")
            
        except Exception as e:
            errors.append(f"状态验证异常: {e}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def migrate_legacy_state(old_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        迁移旧版本状态到新格式
        
        从928项目的状态格式迁移到Stock-trading格式
        """
        try:
            # 创建新的默认状态
            new_state = MartingaleStateManager.create_default_state()
            
            # 迁移方向状态
            for direction in ["long", "short"]:
                if direction in old_state:
                    old_dir = old_state[direction]
                    new_dir = new_state[direction]
                    
                    # 基础字段迁移
                    basic_fields = ["qty", "avg_price", "add_times", "last_qty"]
                    for field in basic_fields:
                        if field in old_dir:
                            new_dir[field] = old_dir[field]
                    
                    # 历史记录迁移
                    if "add_history" in old_dir:
                        new_dir["add_history"] = old_dir["add_history"]
                    
                    # 锁仓状态迁移
                    hedge_state = new_dir["hedge_state"]
                    if "hedge_locked" in old_dir:
                        hedge_state["hedge_locked"] = old_dir["hedge_locked"]
                    if "hedge_stop" in old_dir:
                        hedge_state["hedge_stop"] = old_dir["hedge_stop"]
                    if "locked_profit" in old_dir:
                        hedge_state["locked_profit"] = old_dir["locked_profit"]
            
            # 迁移全局状态
            if "exchange_fault_until" in old_state:
                new_state["global"]["exchange_fault_until"] = old_state["exchange_fault_until"]
            
            # 处理顶层锁仓字段（旧版本可能存在）
            if "hedge_locked" in old_state:
                for direction in ["long", "short"]:
                    new_state[direction]["hedge_state"]["hedge_locked"] = old_state["hedge_locked"]
            
            if "locked_profit" in old_state:
                for direction in ["long", "short"]:
                    new_state[direction]["hedge_state"]["locked_profit"] = old_state["locked_profit"]
            
            logger.log_info("✅ 状态迁移完成：从928格式迁移到Stock-trading格式")
            return new_state
            
        except Exception as e:
            logger.log_error(f"❌ 状态迁移失败：{e}")
            # 迁移失败时返回默认状态
            return MartingaleStateManager.create_default_state()

class MartingaleCalculator:
    """
    马丁对冲策略计算工具
    
    负责各种策略相关的计算：
    1. 加仓数量计算
    2. 止盈止损价格计算
    3. 盈亏计算
    4. 风险度量
    """
    
    @staticmethod
    def calculate_add_quantity(first_qty: float, add_ratio: float, add_times: int) -> float:
        """
        计算下一次加仓数量
        
        公式：next_qty = first_qty * (add_ratio ^ (add_times + 1))
        """
        try:
            result = first_qty * (add_ratio ** (add_times + 1))
            return round(result, 8)  # 保留8位小数精度
        except Exception as e:
            logger.log_warning(f"⚠️ 计算加仓数量异常：{e}")
            return first_qty
    
    @staticmethod
    def calculate_total_position_after_add(first_qty: float, add_ratio: float, add_times: int) -> float:
        """
        计算加仓后的总持仓量
        
        几何级数求和：S_n = first_qty * (add_ratio^(n+1) - 1) / (add_ratio - 1)
        """
        try:
            if add_ratio == 1.0:
                # 特殊情况：等比数列公比为1
                return first_qty * (add_times + 1)
            else:
                result = first_qty * (add_ratio**(add_times + 1) - 1) / (add_ratio - 1)
                return round(result, 8)
        except Exception as e:
            logger.log_warning(f"⚠️ 计算总持仓量异常：{e}")
            return first_qty
    
    @staticmethod
    def calculate_target_add_price(base_price: float, add_interval: float, direction: str) -> float:
        """
        计算加仓触发价格
        
        多头：base_price * (1 - add_interval)
        空头：base_price * (1 + add_interval)
        """
        try:
            if direction.lower() == "long":
                return base_price * (1 - add_interval)
            else:
                return base_price * (1 + add_interval)
        except Exception as e:
            logger.log_warning(f"⚠️ 计算加仓触发价异常：{e}")
            return base_price
    
    @staticmethod
    def calculate_take_profit_price(avg_price: float, tp_ratio: float, direction: str) -> float:
        """
        计算止盈价格
        
        多头：avg_price * (1 + tp_ratio)
        空头：avg_price * (1 - tp_ratio)
        """
        try:
            if direction.lower() == "long":
                return avg_price * (1 + tp_ratio)
            else:
                return avg_price * (1 - tp_ratio)
        except Exception as e:
            logger.log_warning(f"⚠️ 计算止盈价格异常：{e}")
            return avg_price
    
    @staticmethod
    def calculate_unrealized_pnl(qty: float, avg_price: float, current_price: float, direction: str) -> float:
        """
        计算未实现盈亏
        
        多头：(current_price - avg_price) * qty
        空头：(avg_price - current_price) * qty
        """
        try:
            if direction.lower() == "long":
                return (current_price - avg_price) * qty
            else:
                return (avg_price - current_price) * qty
        except Exception as e:
            logger.log_warning(f"⚠️ 计算未实现盈亏异常：{e}")
            return 0.0
    
    @staticmethod
    def calculate_profit_ratio(qty: float, avg_price: float, current_price: float, direction: str) -> float:
        """
        计算盈利比例
        
        profit_ratio = unrealized_pnl / (avg_price * qty)
        """
        try:
            if qty <= 0 or avg_price <= 0:
                return 0.0
                
            unrealized_pnl = MartingaleCalculator.calculate_unrealized_pnl(
                qty, avg_price, current_price, direction
            )
            
            position_value = avg_price * qty
            return unrealized_pnl / position_value if position_value > 0 else 0.0
            
        except Exception as e:
            logger.log_warning(f"⚠️ 计算盈利比例异常：{e}")
            return 0.0
    
    @staticmethod
    def calculate_loss_ratio_from_base(base_price: float, current_price: float, direction: str) -> float:
        """
        计算相对基准价的浮亏比例（用于锁仓触发判断）
        
        多头：max(0, (base_price - current_price) / base_price)
        空头：max(0, (current_price - base_price) / base_price)
        """
        try:
            if base_price <= 0:
                return 0.0
            
            if direction.lower() == "long":
                loss_ratio = (base_price - current_price) / base_price
            else:
                loss_ratio = (current_price - base_price) / base_price
            
            return max(0.0, loss_ratio)  # 负值按0处理
            
        except Exception as e:
            logger.log_warning(f"⚠️ 计算浮亏比例异常：{e}")
            return 0.0

class MartingaleRiskManager:
    """
    马丁对冲策略风险管理工具
    
    负责：
    1. 仓位限制检查
    2. 快速加仓风控
    3. 异常冷却期管理
    4. 风险度量和告警
    """
    
    @staticmethod
    def check_position_limit(current_qty: float, add_qty: float, max_total_qty: Optional[float]) -> Tuple[bool, str]:
        """
        检查仓位限制
        
        Returns:
            (是否通过检查, 说明信息)
        """
        try:
            if max_total_qty is None:
                return True, "无仓位限制"
            
            projected_qty = current_qty + add_qty
            
            if projected_qty > max_total_qty:
                return False, f"预计仓位{projected_qty:.6f}超过上限{max_total_qty:.6f}"
            
            return True, f"仓位检查通过：{projected_qty:.6f}/{max_total_qty:.6f}"
            
        except Exception as e:
            logger.log_warning(f"⚠️ 仓位限制检查异常：{e}")
            return False, f"检查异常: {e}"
    
    @staticmethod
    def should_pause_fast_add(last_add_time: Optional[int], fast_add_window: int = 300) -> Tuple[bool, int]:
        """
        检查是否应该因快速加仓而暂停
        
        Args:
            last_add_time: 上次加仓时间戳
            fast_add_window: 快速加仓检测窗口（秒）
            
        Returns:
            (是否应该暂停, 剩余冷却秒数)
        """
        try:
            if last_add_time is None:
                return False, 0
            
            now_ts = int(time.time())
            time_since_last = now_ts - last_add_time
            
            if time_since_last < fast_add_window:
                remaining = fast_add_window - time_since_last
                return True, remaining
            
            return False, 0
            
        except Exception as e:
            logger.log_warning(f"⚠️ 快速加仓检查异常：{e}")
            return False, 0
    
    @staticmethod
    def calculate_margin_usage(long_qty: float, long_avg: float, short_qty: float, short_avg: float,
                             leverage: float = 1.0) -> Dict[str, float]:
        """
        计算保证金使用情况
        
        Returns:
            包含保证金使用信息的字典
        """
        try:
            long_notional = long_qty * long_avg if long_avg > 0 else 0
            short_notional = short_qty * short_avg if short_avg > 0 else 0
            total_notional = long_notional + short_notional
            
            # 简化计算：假设同等杠杆
            margin_used = total_notional / leverage if leverage > 0 else total_notional
            
            return {
                "long_notional": long_notional,
                "short_notional": short_notional,
                "total_notional": total_notional,
                "margin_used": margin_used,
                "leverage": leverage
            }
            
        except Exception as e:
            logger.log_warning(f"⚠️ 保证金计算异常：{e}")
            return {
                "long_notional": 0,
                "short_notional": 0,
                "total_notional": 0,
                "margin_used": 0,
                "leverage": 1.0
            }
    
    @staticmethod
    def assess_risk_level(state: Dict[str, Any], current_price: float) -> str:
        """
        评估当前风险等级
        
        Returns:
            风险等级字符串：LOW/MEDIUM/HIGH/CRITICAL
        """
        try:
            # 检查锁仓状态
            long_locked = state.get("long", {}).get("hedge_state", {}).get("hedge_locked", False)
            short_locked = state.get("short", {}).get("hedge_state", {}).get("hedge_stop", False)
            
            if long_locked or short_locked:
                return "HIGH"  # 锁仓状态风险较高
            
            # 检查持仓情况
            long_qty = state.get("long", {}).get("qty", 0)
            short_qty = state.get("short", {}).get("qty", 0)
            
            if long_qty == 0 and short_qty == 0:
                return "LOW"  # 无持仓风险最低
            
            # 检查加仓次数
            long_add_times = state.get("long", {}).get("add_times", 0)
            short_add_times = state.get("short", {}).get("add_times", 0)
            max_add_times = max(long_add_times, short_add_times)
            
            if max_add_times >= 3:
                return "HIGH"  # 满仓或接近满仓
            elif max_add_times >= 1:
                return "MEDIUM"  # 已加仓
            else:
                return "LOW"  # 仅首仓
            
        except Exception as e:
            logger.log_warning(f"⚠️ 风险评估异常：{e}")
            return "UNKNOWN"

def format_state_summary(state: Dict[str, Any]) -> str:
    """
    格式化状态摘要（用于日志输出）
    
    生成易读的中文状态摘要
    """
    try:
        lines = []
        lines.append("📊 策略状态摘要")
        lines.append("=" * 40)
        
        for direction in ["long", "short"]:
            if direction not in state:
                continue
                
            dir_state = state[direction]
            dir_name = "多头" if direction == "long" else "空头"
            
            qty = dir_state.get("qty", 0)
            avg_price = dir_state.get("avg_price", 0)
            add_times = dir_state.get("add_times", 0)
            
            hedge_state = dir_state.get("hedge_state", {})
            hedge_locked = hedge_state.get("hedge_locked", False)
            hedge_stop = hedge_state.get("hedge_stop", False)
            locked_profit = hedge_state.get("locked_profit", 0)
            
            lines.append(f"{dir_name}:")
            lines.append(f"  持仓: {qty:.6f} @ {avg_price:.4f}")
            lines.append(f"  加仓: {add_times}次")
            
            if hedge_locked or hedge_stop:
                lines.append(f"  🔒 锁仓状态: 锁定={hedge_locked}, 停机={hedge_stop}")
                if locked_profit > 0:
                    lines.append(f"  💰 锁定利润: {locked_profit:.4f}")
            else:
                lines.append("  🟢 正常状态")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"状态摘要生成失败: {e}"

def validate_strategy_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证策略配置的完整性和有效性
    
    Returns:
        (配置是否有效, 错误信息列表)
    """
    errors = []
    
    try:
        # 检查必需的顶层字段
        required_top_keys = ["symbol", "long", "short", "hedge"]
        for key in required_top_keys:
            if key not in config:
                errors.append(f"缺少必需配置: {key}")
        
        # 检查方向配置
        for direction in ["long", "short"]:
            if direction not in config:
                continue
                
            dir_config = config[direction]
            required_fields = ["first_qty", "add_ratio", "add_interval", "max_add_times"]
            
            for field in required_fields:
                if field not in dir_config:
                    errors.append(f"缺少{direction}.{field}")
                    continue
                
                value = dir_config[field]
                
                # 数值有效性检查
                if field == "first_qty" and (not isinstance(value, (int, float)) or value <= 0):
                    errors.append(f"{direction}.{field} 必须为正数")
                elif field == "add_ratio" and (not isinstance(value, (int, float)) or value < 1):
                    errors.append(f"{direction}.{field} 必须>=1")
                elif field == "add_interval" and (not isinstance(value, (int, float)) or value <= 0 or value >= 1):
                    errors.append(f"{direction}.{field} 必须在(0,1)范围内")
                elif field == "max_add_times" and (not isinstance(value, int) or value < 0):
                    errors.append(f"{direction}.{field} 必须为非负整数")
        
        # 检查对冲配置
        if "hedge" in config:
            hedge_config = config["hedge"]
            
            if "trigger_loss" not in hedge_config:
                errors.append("缺少hedge.trigger_loss")
            else:
                trigger_loss = hedge_config["trigger_loss"]
                if not isinstance(trigger_loss, (int, float)) or trigger_loss <= 0 or trigger_loss >= 1:
                    errors.append("hedge.trigger_loss 必须在(0,1)范围内")
        
        # 检查交易对格式
        if "symbol" in config:
            symbol = config["symbol"]
            if not isinstance(symbol, str) or len(symbol) < 3:
                errors.append("symbol 格式无效")
    
    except Exception as e:
        errors.append(f"配置验证异常: {e}")
    
    return len(errors) == 0, errors