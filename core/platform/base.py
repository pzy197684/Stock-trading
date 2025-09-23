from abc import ABC, abstractmethod
from typing import Dict, Optional

class ExchangeIf(ABC):
    @abstractmethod
    def name(self) -> str:
        """平台名称"""
        pass

    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """平台能力（是否支持对冲、币/张单位等）"""
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> dict:
        """获取指定交易对的仓位信息"""
        pass

    @abstractmethod
    def place_order(self, order_req: dict) -> dict:
        """执行下单请求"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> dict:
        """取消指定订单"""
        pass
