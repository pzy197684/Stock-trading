"""
账户配置管理器
负责加载和验证API密钥配置
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)


class AccountManager:
    """账户配置管理器"""
    
    def __init__(self, accounts_dir: str = "accounts"):
        self.accounts_dir = Path(accounts_dir)
        if not self.accounts_dir.exists():
            raise FileNotFoundError(f"Accounts directory not found: {accounts_dir}")
    
    def load_account_config(self, account_name: str) -> Dict[str, Any]:
        """
        加载指定账户的配置信息
        
        Args:
            account_name: 账户名称 (如 BN_MARTINGALE_001)
            
        Returns:
            账户配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误或缺少必要字段
        """
        account_dir = self.accounts_dir / account_name
        config_file = account_dir / "binance_api.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Account config not found: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证必要字段
            self._validate_config(config, account_name)
            
            # 添加账户名称到配置中
            config['account_name'] = account_name
            
            logger.info(f"Loaded account config: {account_name}")
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load account config {account_name}: {e}")
            raise
    
    def _validate_config(self, config: Dict[str, Any], account_name: str) -> None:
        """验证配置文件格式"""
        required_fields = ['API_KEY', 'API_SECRET']
        
        for field in required_fields:
            if field not in config or not config[field]:
                raise ValueError(f"Missing required field '{field}' in account {account_name}")
            
            # 检查是否为模板占位符
            if 'your_' in config[field].lower() or 'demo_' in config[field].lower():
                raise ValueError(f"Please replace template value for '{field}' in account {account_name}")
        
        # 验证设置部分
        if 'settings' not in config:
            raise ValueError(f"Missing 'settings' section in account {account_name}")
        
        settings = config['settings']
        required_settings = ['exchange', 'api_type', 'testnet']
        
        for setting in required_settings:
            if setting not in settings:
                raise ValueError(f"Missing setting '{setting}' in account {account_name}")
        
        # 验证交易所类型
        if settings['exchange'] != 'binance':
            raise ValueError(f"Unsupported exchange: {settings['exchange']}")
        
        # 验证API类型
        if settings['api_type'] != 'futures':
            raise ValueError(f"Unsupported API type: {settings['api_type']}")
    
    def list_accounts(self) -> list[str]:
        """列出所有可用的账户"""
        accounts = []
        
        for account_dir in self.accounts_dir.iterdir():
            if account_dir.is_dir():
                config_file = account_dir / "binance_api.json"
                if config_file.exists():
                    accounts.append(account_dir.name)
        
        return sorted(accounts)
    
    def get_api_credentials(self, account_name: str) -> Dict[str, str]:
        """
        获取指定账户的API凭证
        
        Args:
            account_name: 账户名称
            
        Returns:
            包含API_KEY和API_SECRET的字典
        """
        config = self.load_account_config(account_name)
        
        return {
            'API_KEY': config['API_KEY'],
            'API_SECRET': config['API_SECRET']
        }
    
    def get_exchange_settings(self, account_name: str) -> Dict[str, Any]:
        """
        获取指定账户的交易所设置
        
        Args:
            account_name: 账户名称
            
        Returns:
            交易所设置字典
        """
        config = self.load_account_config(account_name)
        return config.get('settings', {})
    
    def is_testnet(self, account_name: str) -> bool:
        """检查账户是否为测试网络"""
        settings = self.get_exchange_settings(account_name)
        return settings.get('testnet', False)


# 全局账户管理器实例
account_manager = AccountManager()


def get_account_config(account_name: str) -> Dict[str, Any]:
    """获取账户配置的便捷函数"""
    return account_manager.load_account_config(account_name)


def get_api_credentials(account_name: str) -> Dict[str, str]:
    """获取API凭证的便捷函数"""
    return account_manager.get_api_credentials(account_name)


if __name__ == "__main__":
    # 测试代码
    try:
        manager = AccountManager()
        accounts = manager.list_accounts()
        print(f"Available accounts: {accounts}")
        
        for account in accounts:
            try:
                config = manager.load_account_config(account)
                testnet = manager.is_testnet(account)
                print(f"Account {account}: testnet={testnet}")
            except Exception as e:
                print(f"Error loading {account}: {e}")
                
    except Exception as e:
        print(f"Failed to initialize AccountManager: {e}")