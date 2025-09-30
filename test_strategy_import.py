#!/usr/bin/env python3
# 测试策略导入
import sys
import os
sys.path.insert(0, r'd:\psw\Stock-trading')

try:
    print("开始测试策略导入...")
    
    # 测试基本导入
    print("1. 测试基础模块导入...")
    from core.strategy.base import StrategyBase
    print("   ✅ StrategyBase 导入成功")
    
    # 测试策略模块导入
    print("2. 测试策略模块导入...")
    import core.strategy.martingale_hedge
    print("   ✅ martingale_hedge 模块导入成功")
    
    # 测试策略类导入
    print("3. 测试策略类导入...")
    from core.strategy.martingale_hedge import MartingaleHedgeStrategy
    print(f"   ✅ MartingaleHedgeStrategy 导入成功: {MartingaleHedgeStrategy}")
    
    print("\n🎉 所有导入测试成功！")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()