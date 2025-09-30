#!/usr/bin/env python3
"""
Recovery策略集成验证脚本
验证所有recovery相关文件是否正确创建并且语法正确
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {description}: {file_path} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {file_path} - 文件不存在")
        return False

def check_json_file(file_path, description):
    """检查JSON文件语法"""
    if not check_file_exists(file_path, description):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"   JSON语法正确")
        return True
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON语法错误: {e}")
        return False

def check_python_syntax(file_path, description):
    """检查Python文件语法"""
    if not check_file_exists(file_path, description):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, file_path, 'exec')
        print(f"   Python语法正确")
        return True
    except SyntaxError as e:
        print(f"   ❌ Python语法错误: {e}")
        return False

def main():
    print("=" * 60)
    print("Recovery策略集成验证")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    total_checks = 0
    passed_checks = 0
    
    # 检查核心策略文件
    print("\n📁 核心策略文件:")
    recovery_files = [
        ("core/strategy/recovery/__init__.py", "Recovery模块初始化"),
        ("core/strategy/recovery/strategy.py", "Recovery策略主文件"),
        ("core/strategy/recovery/executor.py", "Recovery执行器"),
        ("core/strategy/recovery/recovery_state_persister.py", "Recovery状态持久化管理器"),
        ("core/strategy/recovery/README.md", "Recovery文档"),
    ]
    
    for file_path, desc in recovery_files:
        full_path = base_dir / file_path
        if file_path.endswith('.py'):
            if check_python_syntax(str(full_path), desc):
                passed_checks += 1
        else:
            if check_file_exists(str(full_path), desc):
                passed_checks += 1
        total_checks += 1
    
    # 检查适配器文件
    print("\n📁 交易所适配器:")
    adapter_files = [
        ("core/strategy/recovery/adapters/__init__.py", "适配器模块初始化"),
        ("core/strategy/recovery/adapters/binance.py", "Binance适配器"),
    ]
    
    for file_path, desc in adapter_files:
        full_path = base_dir / file_path
        if check_python_syntax(str(full_path), desc):
            passed_checks += 1
        total_checks += 1
    
    # 检查插件配置
    print("\n📁 插件配置:")
    plugin_files = [
        ("core/strategy/plugins/recovery.json", "Recovery插件配置"),
    ]
    
    for file_path, desc in plugin_files:
        full_path = base_dir / file_path
        if check_json_file(str(full_path), desc):
            passed_checks += 1
        total_checks += 1
    
    # 检查账户配置
    print("\n📁 账户配置:")
    account_files = [
        ("accounts/BN_RECOVERY_001/template_binance_api.json", "Binance API模板"),
        ("accounts/BN_RECOVERY_001/account_settings.json", "账户设置"),
    ]
    
    for file_path, desc in account_files:
        full_path = base_dir / file_path
        if check_json_file(str(full_path), desc):
            passed_checks += 1
        total_checks += 1
    
    # 检查配置示例
    print("\n📁 配置示例:")
    config_files = [
        ("profiles/DEMO_RECOVERY/config.json", "Recovery策略配置示例"),
    ]
    
    for file_path, desc in config_files:
        full_path = base_dir / file_path
        if check_json_file(str(full_path), desc):
            passed_checks += 1
        total_checks += 1
    
    # 检查测试文件
    print("\n📁 测试文件:")
    test_files = [
        ("core/strategy/recovery/test_recovery_basic.py", "基础功能测试"),
    ]
    
    for file_path, desc in test_files:
        full_path = base_dir / file_path
        if check_python_syntax(str(full_path), desc):
            passed_checks += 1
        total_checks += 1
    
    # 检查文档
    print("\n📁 文档文件:")
    doc_files = [
        ("RECOVERY_INTEGRATION_SUMMARY.md", "集成总结文档"),
    ]
    
    for file_path, desc in doc_files:
        full_path = base_dir / file_path
        if check_file_exists(str(full_path), desc):
            passed_checks += 1
        total_checks += 1
    
    # 总结
    print("\n" + "=" * 60)
    print(f"验证完成: {passed_checks}/{total_checks} 通过")
    
    if passed_checks == total_checks:
        print("🎉 所有文件验证通过！Recovery策略集成成功！")
        return 0
    else:
        print(f"⚠️  有 {total_checks - passed_checks} 个文件未通过验证")
        return 1

if __name__ == "__main__":
    sys.exit(main())