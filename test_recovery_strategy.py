# -*- coding: utf-8 -*-
# test_recovery_strategy.py
# 功能：测试解套策略的基本功能

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategy.recovery.strategy import RecoveryStrategy, RecoveryPlan, RecoveryState
from core.strategy.base import StrategyContext, TradingSignal, SignalType, StrategyStatus
from core.domain.enums import PositionField
import json

def test_recovery_strategy_basic():
    """测试解套策略基本功能"""
    print("🧪 开始测试解套策略基本功能...")
    
    # 创建测试配置
    config = {
        "symbol": "ETHUSDT",
        "recovery": {
            "mode": "long_trapped",
            "cap_ratio": 0.6,
            "ttl_seconds": 300,
            "use_limit_tp": True,
            "grid": {
                "add_interval_pct": 0.04,
                "tp_first_order_pct": 0.015,
                "tp_before_full_pct": 0.025,
                "tp_after_full_pct": 0.015,
                "tp_reprice_tol_ratio": 0.001,
                "martingale": {
                    "first_qty": 30.0,
                    "multiplier": 1.8,
                    "max_add_times": 4
                }
            },
            "confirm": {
                "kline": "15m",
                "filters": {
                    "body_min_frac_of_interval": 0.3,
                    "wick_to_body_max": 1.8,
                    "followthrough_window_min": 20
                }
            },
            "circuit_breakers": {
                "jump": {
                    "enabled": True,
                    "window_minutes": 25,
                    "factor_vs_interval": 2.5,
                    "pause_minutes": 20
                },
                "atr": {
                    "enabled": True,
                    "tf": "1h",
                    "factor_vs_interval": 2.8,
                    "pause_hours": 12
                }
            }
        }
    }
    
    # 创建策略实例
    strategy = RecoveryStrategy(config)
    
    # 测试参数验证
    print("1. 测试参数验证...")
    required_params = strategy.get_required_params()
    print(f"   必需参数: {required_params}")
    
    errors = strategy.validate_params(config)
    if errors:
        print(f"   ❌ 参数验证失败: {errors}")
        return False
    else:
        print("   ✅ 参数验证通过")
    
    # 测试策略初始化
    print("2. 测试策略初始化...")
    
    # 创建模拟上下文
    context = StrategyContext(
        symbol="ETHUSDT",
        current_price=2500.0,
        current_time=1234567890,
        balance={'total_balance': 10000.0, 'available_balance': 8000.0},
        position_long={
            PositionField.QUANTITY.value: 100.0,  # 多头被套100个单位
            PositionField.AVERAGE_PRICE.value: 2600.0,  # 均价2600，当前价2500，被套中
            PositionField.UNREALIZED_PNL.value: -10000.0
        },
        position_short={
            PositionField.QUANTITY.value: 0.0,
            PositionField.AVERAGE_PRICE.value: 0.0,
            PositionField.UNREALIZED_PNL.value: 0.0
        }
    )
    
    init_result = strategy.initialize(context)
    if init_result:
        print("   ✅ 策略初始化成功")
        print(f"   策略状态: {strategy.status}")
    else:
        print("   ❌ 策略初始化失败")
        return False
    
    # 测试信号生成
    print("3. 测试信号生成...")
    
    # 场景1: 首次运行，应该开启首仓
    print("   场景1: 首次运行 (空头首仓开启)")
    signal = strategy.generate_signal(context)
    print(f"   信号类型: {signal.signal_type}")
    print(f"   信号原因: {signal.reason}")
    print(f"   交易数量: {signal.quantity}")
    if signal.metadata:
        print(f"   元数据: {signal.metadata}")
    
    # 模拟首仓成交，更新状态
    strategy.short_state.qty = 30.0
    strategy.short_state.avg_price = 2500.0
    strategy.short_state.last_qty = 30.0
    strategy.short_state.last_fill_price = 2500.0
    strategy.short_state.add_times = 0
    
    # 场景2: 价格下跌，触发加仓
    print("\n   场景2: 价格下跌触发加仓")
    context.current_price = 2400.0  # 价格下跌4%
    signal = strategy.generate_signal(context)
    print(f"   信号类型: {signal.signal_type}")
    print(f"   信号原因: {signal.reason}")
    print(f"   交易数量: {signal.quantity}")
    
    # 模拟加仓成交
    old_qty = strategy.short_state.qty
    add_qty = 30.0 * 1.8  # 按倍率加仓
    new_avg = (old_qty * strategy.short_state.avg_price + add_qty * 2400.0) / (old_qty + add_qty)
    strategy.short_state.qty += add_qty
    strategy.short_state.avg_price = new_avg
    strategy.short_state.add_times += 1
    strategy.short_state.last_qty = add_qty
    strategy.short_state.last_fill_price = 2400.0
    
    # 场景3: 价格反弹，触发止盈
    print("\n   场景3: 价格反弹触发止盈")
    context.current_price = 2350.0  # 价格反弹，满足止盈条件
    signal = strategy.generate_signal(context)
    print(f"   信号类型: {signal.signal_type}")
    print(f"   信号原因: {signal.reason}")
    print(f"   交易数量: {signal.quantity}")
    print(f"   止盈价格: {signal.price}")
    
    print("\n✅ 解套策略基本功能测试完成")
    return True

def test_recovery_plan():
    """测试解套计划数据结构"""
    print("🧪 测试解套计划数据结构...")
    
    plan = RecoveryPlan(
        action="add",
        side="short",
        qty=54.0,
        price=2400.0,
        step=1,
        reason="满足间距与确认条件"
    )
    
    print(f"   执行计划: {plan.action}")
    print(f"   交易方向: {plan.side}")
    print(f"   交易数量: {plan.qty}")
    print(f"   轮次: {plan.step}")
    print(f"   原因: {plan.reason}")
    
    print("✅ 解套计划测试完成")

def test_recovery_state():
    """测试解套状态数据结构"""
    print("🧪 测试解套状态数据结构...")
    
    state = RecoveryState()
    print(f"   初始状态: qty={state.qty}, avg_price={state.avg_price}")
    print(f"   加仓次数: {state.add_times}")
    print(f"   容量: {state.cap}")
    print(f"   是否满仓: {state.at_full}")
    print(f"   挂单记录: {state.pending_tp}")
    
    # 更新状态
    state.qty = 100.0
    state.avg_price = 2450.0
    state.add_times = 2
    state.trapped_qty = 100.0
    state.cap = 75.0
    state.at_full = True
    
    print(f"   更新后状态: qty={state.qty}, avg_price={state.avg_price}")
    print(f"   加仓次数: {state.add_times}")
    print(f"   是否满仓: {state.at_full}")
    
    print("✅ 解套状态测试完成")

def print_strategy_info():
    """打印策略信息"""
    print("📊 解套策略信息:")
    print("   策略名称: Recovery Strategy (解套策略)")
    print("   策略类型: 马丁格尔解套策略")
    print("   支持模式: long_trapped (多头被套), short_trapped (空头被套)")
    print("   核心功能:")
    print("     - 马丁格尔加仓")
    print("     - 分层止盈")
    print("     - 容量控制")
    print("     - 熔断保护")
    print("     - K线确认")
    print("   风险等级: 中高风险")
    print("   适用场景: 震荡市场解套")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 解套策略测试程序")
    print("=" * 60)
    
    try:
        print_strategy_info()
        print()
        
        test_recovery_plan()
        print()
        
        test_recovery_state()
        print()
        
        test_recovery_strategy_basic()
        print()
        
        print("=" * 60)
        print("🎉 所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()