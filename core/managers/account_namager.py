# core/managers/account_manager.py
from typing import Dict
from core.domain.models import OrderReq
from core.platform.base import ExchangeIf
from core.platform.binance import BinanceExchange
from core.platform.coinw import CoinWExchange
from core.platform.okx import OKXExchange

class AccountManager:
    def __init__(self):
        self.accounts = {}

    def add_account(self, platform_name: str, account_info: Dict):
        """添加账号并关联到平台"""
        self.accounts[platform_name] = account_info

    def get_account(self, platform_name: str):
        """根据平台名称获取账号信息"""
        return self.accounts.get(platform_name)

    def create_exchange_instance(self, platform_name: str, api_key: str, api_secret: str) -> ExchangeIf:
        """根据平台名称和API密钥创建平台实例"""
        account_info = self.get_account(platform_name)
        if not account_info:
            raise ValueError(f"账号未找到：{platform_name}")
        
        # 使用api_key和api_secret等信息创建平台实例
        # 假设我们已有各平台的适配器，如 BinanceExchange、CoinWExchange 等
        platform_class = self._get_platform_class(platform_name)
        return platform_class(api_key=api_key, api_secret=api_secret)

    def _get_platform_class(self, platform_name: str) -> ExchangeIf:
        """获取平台适配器类"""
        platform_classes = {
            "binance": BinanceExchange,
            "coinw": CoinWExchange,
            "okx": OKXExchange,
        }
        return platform_classes.get(platform_name,ExchangeIf)
