# -*- coding: utf-8 -*-
# accounts/account_manager.py
# 功能：账户和API密钥管理器

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

class AccountManager:
    """
    账户管理器
    
    负责：
    1. 加载和管理API密钥
    2. 账户配置管理
    3. 安全验证和权限检查
    4. 环境切换（测试/实盘）
    """
    
    def __init__(self, accounts_dir: str = None):
        """
        初始化账户管理器
        
        Args:
            accounts_dir: accounts目录路径，默认为当前目录的accounts文件夹
        """
        if accounts_dir is None:
            # 自动检测accounts目录
            current_dir = Path(__file__).parent
            self.accounts_dir = current_dir
        else:
            self.accounts_dir = Path(accounts_dir)
        
        if not self.accounts_dir.exists():
            raise FileNotFoundError(f"Accounts目录不存在: {self.accounts_dir}")
        
        self._cache = {}  # 缓存已加载的配置
    
    def list_accounts(self) -> List[str]:
        """
        列出所有可用的账户
        
        Returns:
            账户名称列表
        """
        accounts = []
        for item in self.accounts_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                accounts.append(item.name)
        
        return sorted(accounts)
    
    def load_api_keys(self, account_name: str, exchange: str = "binance") -> Tuple[bool, Dict[str, Any]]:
        """
        加载指定账户的API密钥
        
        Args:
            account_name: 账户名称
            exchange: 交易所名称
            
        Returns:
            (成功标志, 密钥数据或错误信息)
        """
        try:
            # 构建API密钥文件路径
            api_file = self.accounts_dir / account_name / f"{exchange}_api.json"
            
            if not api_file.exists():
                return False, {"error": f"API密钥文件不存在: {api_file}"}
            
            # 读取API密钥
            with open(api_file, 'r', encoding='utf-8') as f:
                api_data = json.load(f)
            
            # 验证必需字段
            required_fields = ["API_KEY", "API_SECRET"]
            missing_fields = [field for field in required_fields if field not in api_data or not api_data[field]]
            
            if missing_fields:
                return False, {"error": f"缺少必需的API密钥字段: {missing_fields}"}
            
            # 检查是否是模板文件
            if "your_" in api_data["API_KEY"].lower() or "template" in api_data["API_KEY"].lower():
                return False, {"error": "API密钥似乎是模板文件，请填入实际密钥"}
            
            # 缓存数据
            cache_key = f"{account_name}_{exchange}"
            self._cache[cache_key] = api_data
            
            return True, api_data
            
        except json.JSONDecodeError as e:
            return False, {"error": f"JSON格式错误: {e}"}
        except Exception as e:
            return False, {"error": f"加载API密钥失败: {e}"}
    
    def load_account_settings(self, account_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        加载账户设置
        
        Args:
            account_name: 账户名称
            
        Returns:
            (成功标志, 设置数据或错误信息)
        """
        try:
            settings_file = self.accounts_dir / account_name / "account_settings.json"
            
            if not settings_file.exists():
                return False, {"error": f"账户设置文件不存在: {settings_file}"}
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            
            return True, settings_data
            
        except Exception as e:
            return False, {"error": f"加载账户设置失败: {e}"}
    
    def validate_account(self, account_name: str, exchange: str = "binance") -> Tuple[bool, str]:
        """
        验证账户配置的完整性
        
        Args:
            account_name: 账户名称
            exchange: 交易所名称
            
        Returns:
            (验证是否通过, 验证消息)
        """
        # 检查账户目录
        account_dir = self.accounts_dir / account_name
        if not account_dir.exists():
            return False, f"账户目录不存在: {account_name}"
        
        # 检查API密钥
        success, api_data = self.load_api_keys(account_name, exchange)
        if not success:
            return False, f"API密钥验证失败: {api_data.get('error', '未知错误')}"
        
        # 检查账户设置
        success, settings_data = self.load_account_settings(account_name)
        if not success:
            return False, f"账户设置验证失败: {settings_data.get('error', '未知错误')}"
        
        return True, "账户验证通过"
    
    def get_account_info(self, account_name: str) -> Dict[str, Any]:
        """
        获取账户完整信息
        
        Args:
            account_name: 账户名称
            
        Returns:
            账户信息字典
        """
        result = {
            "account_name": account_name,
            "exists": False,
            "api_keys": {},
            "settings": {},
            "validation": {"passed": False, "message": ""}
        }
        
        # 检查账户是否存在
        account_dir = self.accounts_dir / account_name
        if not account_dir.exists():
            result["validation"]["message"] = "账户目录不存在"
            return result
        
        result["exists"] = True
        
        # 加载账户设置
        success, settings = self.load_account_settings(account_name)
        if success:
            result["settings"] = settings
        
        # 检查可用的API密钥文件
        for api_file in account_dir.glob("*_api.json"):
            if api_file.name.startswith("template_"):
                continue  # 跳过模板文件
                
            exchange = api_file.name.replace("_api.json", "")
            success, api_data = self.load_api_keys(account_name, exchange)
            result["api_keys"][exchange] = {
                "available": success,
                "error": api_data.get("error") if not success else None
            }
        
        # 执行验证
        validation_success, validation_message = self.validate_account(account_name)
        result["validation"] = {
            "passed": validation_success,
            "message": validation_message
        }
        
        return result
    
    def create_account_template(self, account_name: str, exchange: str = "binance", 
                              environment: str = "testnet") -> bool:
        """
        创建新账户的模板文件
        
        Args:
            account_name: 新账户名称
            exchange: 交易所名称
            environment: 环境类型
            
        Returns:
            创建是否成功
        """
        try:
            account_dir = self.accounts_dir / account_name
            account_dir.mkdir(exist_ok=True)
            
            # 创建API密钥模板
            api_template = {
                "API_KEY": f"your_{exchange}_api_key_here",
                "API_SECRET": f"your_{exchange}_api_secret_here",
                "API_PASSPHRASE": "",
                "notes": {
                    "exchange": exchange,
                    "environment": environment,
                    "permissions": ["futures_trading"],
                    "created_date": "2025-09-29",
                    "description": f"{exchange.title()} API密钥模板 - 请替换为实际密钥"
                },
                "settings": {
                    "testnet": environment == "testnet",
                    "base_url": f"https://{'testnet.' if environment == 'testnet' else ''}api.{exchange}.com",
                    "timeout": 30,
                    "retry_count": 3
                }
            }
            
            api_file = account_dir / f"template_{exchange}_api.json"
            with open(api_file, 'w', encoding='utf-8') as f:
                json.dump(api_template, f, indent=2, ensure_ascii=False)
            
            # 创建账户设置模板
            settings_template = {
                "account_name": account_name,
                "description": f"{account_name} 账户配置",
                "platform": exchange,
                "environment": environment,
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
            
            return True
            
        except Exception as e:
            print(f"创建账户模板失败: {e}")
            return False
    
    def export_account_summary(self) -> Dict[str, Any]:
        """
        导出所有账户的摘要信息
        
        Returns:
            账户摘要字典
        """
        summary = {
            "total_accounts": 0,
            "accounts": {},
            "statistics": {
                "testnet_accounts": 0,
                "live_accounts": 0,
                "validated_accounts": 0,
                "error_accounts": 0
            }
        }
        
        accounts = self.list_accounts()
        summary["total_accounts"] = len(accounts)
        
        for account_name in accounts:
            account_info = self.get_account_info(account_name)
            summary["accounts"][account_name] = {
                "exists": account_info["exists"],
                "platform": account_info.get("settings", {}).get("platform", "unknown"),
                "environment": account_info.get("settings", {}).get("environment", "unknown"),
                "validation_passed": account_info["validation"]["passed"],
                "api_keys_count": len(account_info["api_keys"])
            }
            
            # 统计信息
            if account_info["validation"]["passed"]:
                summary["statistics"]["validated_accounts"] += 1
            else:
                summary["statistics"]["error_accounts"] += 1
                
            env = account_info.get("settings", {}).get("environment", "")
            if env == "testnet":
                summary["statistics"]["testnet_accounts"] += 1
            elif env == "live":
                summary["statistics"]["live_accounts"] += 1
        
        return summary


def main():
    """简单的命令行工具用于管理账户"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python account_manager.py <command> [args]")
        print("命令:")
        print("  list                     - 列出所有账户")
        print("  info <account_name>      - 显示账户信息")
        print("  validate <account_name>  - 验证账户配置")
        print("  summary                  - 显示账户摘要")
        return
    
    try:
        manager = AccountManager()
        command = sys.argv[1]
        
        if command == "list":
            accounts = manager.list_accounts()
            print(f"找到 {len(accounts)} 个账户:")
            for account in accounts:
                print(f"  - {account}")
        
        elif command == "info" and len(sys.argv) > 2:
            account_name = sys.argv[2]
            info = manager.get_account_info(account_name)
            print(json.dumps(info, indent=2, ensure_ascii=False))
        
        elif command == "validate" and len(sys.argv) > 2:
            account_name = sys.argv[2]
            success, message = manager.validate_account(account_name)
            print(f"验证结果: {'通过' if success else '失败'}")
            print(f"消息: {message}")
        
        elif command == "summary":
            summary = manager.export_account_summary()
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        
        else:
            print("未知命令或缺少参数")
    
    except Exception as e:
        print(f"执行失败: {e}")


if __name__ == "__main__":
    main()