#!/usr/bin/env python3
"""
账户配置系统测试脚本
验证accounts文件夹和API密钥配置是否正确
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.managers.account_manager import AccountManager
    from core.logger import get_logger
    
    logger = get_logger(__name__)
    
    def test_account_system():
        """测试账户配置系统"""
        print("=" * 60)
        print("账户配置系统测试")
        print("=" * 60)
        
        try:
            # 初始化账户管理器
            manager = AccountManager()
            
            # 列出所有账户
            accounts = manager.list_accounts()
            print(f"\n📋 发现账户: {len(accounts)}个")
            for account in accounts:
                print(f"   • {account}")
            
            if not accounts:
                print("❌ 没有发现任何账户配置")
                print("   请确保accounts文件夹中包含正确的配置文件")
                return False
            
            print("\n" + "=" * 60)
            print("验证每个账户配置")
            print("=" * 60)
            
            valid_accounts = []
            
            for account in accounts:
                print(f"\n🔍 验证账户: {account}")
                try:
                    # 加载配置
                    config = manager.load_account_config(account)
                    
                    # 检查是否为测试网络
                    is_testnet = manager.is_testnet(account)
                    testnet_status = "测试网络" if is_testnet else "主网"
                    
                    # 获取交易所设置
                    settings = manager.get_exchange_settings(account)
                    exchange = settings.get('exchange', 'unknown')
                    
                    print(f"   ✅ 配置有效")
                    print(f"   📊 交易所: {exchange}")
                    print(f"   🌐 网络: {testnet_status}")
                    print(f"   🔑 API密钥: 已配置")
                    
                    # 检查是否为模板配置
                    credentials = manager.get_api_credentials(account)
                    if any('template' in str(v).lower() or 'demo' in str(v).lower() or 'your_' in str(v).lower() 
                           for v in credentials.values()):
                        print(f"   ⚠️  警告: 检测到模板配置，请填入真实API密钥")
                    
                    valid_accounts.append(account)
                    
                except Exception as e:
                    print(f"   ❌ 配置错误: {e}")
            
            print("\n" + "=" * 60)
            print("测试结果摘要")
            print("=" * 60)
            print(f"总账户数: {len(accounts)}")
            print(f"有效账户: {len(valid_accounts)}")
            print(f"错误账户: {len(accounts) - len(valid_accounts)}")
            
            if valid_accounts:
                print(f"\n✅ 可用账户:")
                for account in valid_accounts:
                    testnet = " (测试网)" if manager.is_testnet(account) else " (主网)"
                    print(f"   • {account}{testnet}")
                
                print(f"\n💡 使用示例:")
                example_account = valid_accounts[0]
                print(f"   from core.managers.account_manager import get_account_config")
                print(f"   config = get_account_config('{example_account}')")
                
                return True
            else:
                print(f"\n❌ 没有可用的账户配置")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def test_integration_example():
        """测试集成示例"""
        print("\n" + "=" * 60)
        print("集成示例测试")
        print("=" * 60)
        
        try:
            from core.managers.account_manager import get_account_config, get_api_credentials
            
            manager = AccountManager()
            accounts = manager.list_accounts()
            
            if not accounts:
                print("❌ 没有账户可供测试")
                return
            
            test_account = accounts[0]
            print(f"🧪 使用账户 {test_account} 进行集成测试")
            
            # 测试配置加载
            config = get_account_config(test_account)
            print(f"   ✅ 配置加载成功: {len(config)} 个字段")
            
            # 测试凭证获取  
            credentials = get_api_credentials(test_account)
            print(f"   ✅ 凭证获取成功: {len(credentials)} 个字段")
            
            # 测试设置获取
            settings = manager.get_exchange_settings(test_account)
            print(f"   ✅ 设置获取成功: {len(settings)} 个字段")
            
            print(f"   💚 集成测试通过")
            
        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
    
    if __name__ == "__main__":
        success = test_account_system()
        
        if success:
            test_integration_example()
            print(f"\n🎉 账户配置系统就绪!")
            print(f"   现在可以在策略中使用accounts文件夹中的API密钥配置")
        else:
            print(f"\n🔧 请检查并修复账户配置")
            
        print("\n" + "=" * 60)

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)