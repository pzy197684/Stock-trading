# -*- coding: utf-8 -*-
# test_recovery_basic.py
# 功能：Recovery策略基本功能测试（无需Python环境配置）

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_recovery_import():
    """测试recovery策略是否可以正常导入"""
    try:
        from core.strategy.recovery.strategy import RecoveryStrategy
        print("✅ RecoveryStrategy导入成功")
        return True
    except ImportError as e:
        print(f"❌ RecoveryStrategy导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_recovery_config():
    """测试recovery策略配置验证"""
    try:
        from core.strategy.recovery.strategy import RecoveryStrategy
        
        # 测试配置
        config = {
            "name": "test_recovery",
            "params": {
                "symbol": "ETHUSDT",
                "recovery": {
                    "mode": "long_trapped",
                    "cap_ratio": 0.75,
                    "grid": {
                        "martingale": {
                            "first_qty": 50.0,
                            "multiplier": 2.0,
                            "max_add_times": 4
                        }
                    }
                }
            }
        }
        
        strategy = RecoveryStrategy(config)
        
        # 验证参数
        errors = strategy.validate_params(config["params"])
        if not errors:
            print("✅ 配置验证通过")
            return True
        else:
            print(f"❌ 配置验证失败: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_recovery_plugin():
    """测试recovery插件配置"""
    import json
    try:
        plugin_file = "core/strategy/plugins/recovery.json"
        if os.path.exists(plugin_file):
            with open(plugin_file, 'r', encoding='utf-8') as f:
                plugin_config = json.load(f)
            
            required_fields = ["name", "display_name", "strategy_class"]
            missing = [field for field in required_fields if field not in plugin_config]
            
            if not missing:
                print("✅ 插件配置验证通过")
                return True
            else:
                print(f"❌ 插件配置缺少字段: {missing}")
                return False
        else:
            print(f"❌ 插件文件不存在: {plugin_file}")
            return False
            
    except Exception as e:
        print(f"❌ 插件测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始Recovery策略基本测试...")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_recovery_import),
        ("配置测试", test_recovery_config), 
        ("插件测试", test_recovery_plugin)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Recovery策略集成成功")
        return True
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    main()