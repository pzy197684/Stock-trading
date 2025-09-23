# core/managers/platform_manager.py
from core.platform.base import ExchangeIf
from core.platform.binance import BinanceExchange
from core.platform.coinw import CoinWExchange
from core.platform.okx import OKXExchange

class PlatformManager:
    def __init__(self):
        self.platforms = {
            "binance": BinanceExchange(),
            "coinw": CoinWExchange(),
            "okx": OKXExchange()
        }

    def get_platform(self, platform_name: str) -> ExchangeIf:
        """根据平台名称获取对应的实例"""
        return self.platforms.get(platform_name, ExchangeIf)

    def add_platform(self, platform_name: str, platform_instance):
        """添加新平台"""
        self.platforms[platform_name] = platform_instance
