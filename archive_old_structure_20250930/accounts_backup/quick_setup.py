# -*- coding: utf-8 -*-
# accounts/quick_setup.py  
# 功能：快速账户设置工具，无需Python环境配置

import os
import json
import sys
from pathlib import Path

def create_account_template():
    """创建完整的账户管理结构"""
    try:
        print("开始创建账户管理结构...")
        
        # 获取accounts目录
        accounts_dir = Path(__file__).parent
        print(f"工作目录: {accounts_dir}")
        
        # 创建BN_MARTINGALE_002账户（确保没有冲突）
        account_name = "BN_MARTINGALE_002"
        account_dir = accounts_dir / account_name
        account_dir.mkdir(exist_ok=True)
        print(f"✓ 创建账户目录: {account_dir}")
        
        # 创建API密钥模板
        api_template = {
            "API_KEY": "your_binance_api_key_here",
            "API_SECRET": "your_binance_api_secret_here",
            "API_PASSPHRASE": "",
            "notes": {
                "exchange": "binance",
                "environment": "testnet",
                "permissions": ["futures_trading"],
                "created_date": "2025-09-29",
                "description": "Binance API密钥 - 请替换为实际密钥"
            },
            "settings": {
                "testnet": True,
                "base_url": "https://testnet.binance.vision",
                "timeout": 30,
                "retry_count": 3
            }
        }
        
        # 保存API模板文件
        api_file = account_dir / "template_binance_api.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(api_template, f, indent=2, ensure_ascii=False)
        print(f"✓ 创建API模板: {api_file}")
        
        # 创建账户设置
        settings_template = {
            "account_name": account_name,
            "description": f"{account_name} 马丁对冲策略账户",
            "platform": "binance",
            "environment": "testnet",
            "created_date": "2025-09-29",
            
            "trading_settings": {
                "default_symbol": "ETHUSDT",
                "position_mode": "hedge",
                "margin_type": "isolated", 
                "leverage": 1,
                "max_position_size": 0.1
            },
            
            "risk_limits": {
                "max_daily_loss": 100.0,
                "max_total_position": 1.0,
                "max_open_orders": 10
            },
            
            "notification": {
                "enable_alerts": True,
                "webhook_url": "",
                "email_alerts": False
            }
        }
        
        settings_file = account_dir / "account_settings.json"
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings_template, f, indent=2, ensure_ascii=False)
        print(f"✓ 创建设置文件: {settings_file}")
        
        # 创建.gitignore文件（如果不存在）
        gitignore_file = accounts_dir / ".gitignore"
        if not gitignore_file.exists():
            gitignore_content = """# API密钥安全保护
*_api.json
!template_*_api.json

# 账户特定配置
*/config.local.json
*/state.json

# 日志文件
*.log
logs/

# 临时文件
*.tmp
*.bak
.DS_Store
Thumbs.db
"""
            with open(gitignore_file, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
            print(f"✓ 创建.gitignore: {gitignore_file}")
        
        # 显示后续步骤
        print("\n✓ 账户结构创建完成！")
        print("\n下一步操作:")
        print(f"1. 编辑 {api_file}")
        print("   - 将 'your_binance_api_key_here' 替换为实际API密钥")
        print("   - 将 'your_binance_api_secret_here' 替换为实际API私钥")
        print(f"2. 将文件重命名为: {account_dir / 'binance_api.json'}")
        print(f"3. 根据需要修改 {settings_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ 创建失败: {e}")
        return False

def list_accounts():
    """列出所有账户"""
    try:
        accounts_dir = Path(__file__).parent
        print(f"扫描目录: {accounts_dir}")
        
        accounts = []
        for item in accounts_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name == '__pycache__':
                accounts.append(item.name)
        
        if not accounts:
            print("没有找到任何账户")
            return
        
        print(f"\n找到 {len(accounts)} 个账户:")
        for account in sorted(accounts):
            account_dir = accounts_dir / account
            
            # 检查配置文件
            has_api = any(f.name.endswith('_api.json') for f in account_dir.glob('*'))
            has_settings = (account_dir / 'account_settings.json').exists()
            
            status = "✓" if (has_api and has_settings) else "✗"
            print(f"  {status} {account:25s} [API: {'✓' if has_api else '✗'}] [设置: {'✓' if has_settings else '✗'}]")
    
    except Exception as e:
        print(f"列出账户失败: {e}")

def validate_account(account_name):
    """验证账户配置"""
    try:
        accounts_dir = Path(__file__).parent
        account_dir = accounts_dir / account_name
        
        if not account_dir.exists():
            print(f"✗ 账户目录不存在: {account_name}")
            return False
        
        print(f"验证账户: {account_name}")
        print("=" * 40)
        
        # 检查API密钥文件
        api_files = list(account_dir.glob('*_api.json'))
        if not api_files:
            print("✗ 未找到API密钥文件")
            return False
        
        print(f"✓ 找到 {len(api_files)} 个API密钥文件:")
        for api_file in api_files:
            # 检查是否是模板文件
            is_template = api_file.name.startswith('template_')
            status = "模板" if is_template else "配置"
            print(f"  - {api_file.name} ({status})")
            
            # 读取并验证内容
            try:
                with open(api_file, 'r', encoding='utf-8') as f:
                    api_data = json.load(f)
                
                if not is_template:
                    if 'your_' in api_data.get('API_KEY', '').lower():
                        print(f"    ⚠️ 疑似未配置实际密钥")
                    else:
                        print(f"    ✓ API密钥已配置")
            
            except json.JSONDecodeError:
                print(f"    ✗ JSON格式错误")
            except Exception as e:
                print(f"    ✗ 读取失败: {e}")
        
        # 检查设置文件
        settings_file = account_dir / 'account_settings.json'
        if settings_file.exists():
            print(f"✓ 找到设置文件: {settings_file.name}")
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    platform = settings.get('platform', '未知')
                    env = settings.get('environment', '未知')
                    print(f"  平台: {platform}, 环境: {env}")
            except Exception as e:
                print(f"  ✗ 设置文件读取失败: {e}")
        else:
            print("✗ 设置文件不存在")
            return False
        
        print("✓ 账户验证完成")
        return True
        
    except Exception as e:
        print(f"验证失败: {e}")
        return False

def show_help():
    """显示帮助信息"""
    print("账户快速设置工具")
    print("=" * 30)
    print("使用方法: python quick_setup.py <命令>")
    print("")
    print("命令:")
    print("  create    - 创建新账户模板")
    print("  list      - 列出所有账户")
    print("  validate <账户名>  - 验证账户配置")
    print("  help      - 显示此帮助")
    print("")
    print("示例:")
    print("  python quick_setup.py create")
    print("  python quick_setup.py list")
    print("  python quick_setup.py validate BN_MARTINGALE_001")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "create":
            create_account_template()
        elif command == "list":
            list_accounts()
        elif command == "validate":
            if len(sys.argv) > 2:
                validate_account(sys.argv[2])
            else:
                print("错误: 请指定账户名称")
        elif command == "help":
            show_help()
        else:
            print(f"未知命令: {command}")
            show_help()
    
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"程序异常: {e}")

if __name__ == "__main__":
    main()