# core/strategy/base.py
# 功能：重构后的策略基础接口和抽象类
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class StrategyStatus(Enum):
    """策略状态枚举"""
    INITIALIZED = "initialized"    # 已初始化
    RUNNING = "running"           # 运行中
    PAUSED = "paused"            # 暂停
    STOPPED = "stopped"          # 已停止
    ERROR = "error"              # 错误状态

class SignalType(Enum):
    """交易信号类型"""
    NONE = "none"                # 无信号
    OPEN_LONG = "open_long"      # 开多
    OPEN_SHORT = "open_short"    # 开空
    ADD_LONG = "add_long"        # 加多仓
    ADD_SHORT = "add_short"      # 加空仓
    CLOSE_LONG = "close_long"    # 平多
    CLOSE_SHORT = "close_short"  # 平空
    HEDGE = "hedge"              # 对冲
    TAKE_PROFIT = "take_profit"  # 止盈
    STOP_LOSS = "stop_loss"      # 止损

@dataclass
class TradingSignal:
    """交易信号"""
    signal_type: SignalType
    symbol: str
    quantity: float
    price: Optional[float] = None  # None表示市价单
    reason: str = ""              # 信号原因
    metadata: Optional[Dict[str, Any]] = None  # 额外信息
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class StrategyContext:
    """策略上下文"""
    account: str                           # 账号名
    platform: str                          # 平台名
    symbol: str                           # 交易对
    current_price: float                  # 当前价格
    position_long: Dict[str, Any]         # 多仓信息
    position_short: Dict[str, Any]        # 空仓信息
    balance: Dict[str, Any]               # 余额信息
    market_data: Optional[Dict[str, Any]] = None    # 市场数据
    custom_data: Optional[Dict[str, Any]] = None    # 自定义数据
    exchange: Optional[Any] = None        # 交易所实例，用于下单操作
    
    def __post_init__(self):
        if self.market_data is None:
            self.market_data = {}
        if self.custom_data is None:
            self.custom_data = {}

class StrategyBase(ABC):
    """
    策略基础抽象类
    
    所有策略都应继承此类并实现抽象方法
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化策略
        
        Args:
            config: 策略配置字典，包含参数和元信息
        """
        self.config = config.copy()
        self.name = config.get("name", "Unnamed Strategy")
        self.params = config.get("params", {})
        self.metadata = config.get("metadata", {})
        
        # 策略状态
        self.status = StrategyStatus.INITIALIZED
        self.last_signal: Optional[TradingSignal] = None
        self.last_execution_time: Optional[float] = None
        self.execution_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        
        # 运行时数据
        self.runtime_data = {}
        
        # 验证配置
        self._validate_config()
    
    @abstractmethod
    def get_required_params(self) -> List[str]:
        """返回必需的参数列表"""
        raise NotImplementedError()
    
    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """返回默认参数字典"""
        raise NotImplementedError()
    
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """
        验证参数有效性
        
        Args:
            params: 参数字典
            
        Returns:
            错误信息列表，空列表表示验证通过
        """
        raise NotImplementedError()
    
    @abstractmethod
    def initialize(self, context: StrategyContext) -> bool:
        """
        初始化策略（在开始交易前调用）
        
        Args:
            context: 策略上下文
            
        Returns:
            初始化是否成功
        """
        raise NotImplementedError()
    
    @abstractmethod
    def generate_signal(self, context: StrategyContext) -> TradingSignal:
        """
        生成交易信号
        
        Args:
            context: 策略上下文
            
        Returns:
            交易信号
        """
        raise NotImplementedError()
    
    def on_order_filled(self, order_info: Dict[str, Any], context: StrategyContext):
        """
        订单成交回调（可选重写）
        
        Args:
            order_info: 订单信息
            context: 策略上下文
        """
        pass
    
    def on_order_cancelled(self, order_info: Dict[str, Any], context: StrategyContext):
        """
        订单取消回调（可选重写）
        
        Args:
            order_info: 订单信息
            context: 策略上下文
        """
        pass
    
    def on_error(self, error: Exception, context: StrategyContext):
        """
        错误处理回调（可选重写）
        
        Args:
            error: 错误对象
            context: 策略上下文
        """
        self.error_count += 1
        self.last_error = str(error)
        self.status = StrategyStatus.ERROR
    
    def cleanup(self, context: StrategyContext):
        """
        清理资源（策略停止时调用，可选重写）
        
        Args:
            context: 策略上下文
        """
        pass
    
    # 公共辅助方法
    def get_param(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.params.get(key, default)
    
    def set_param(self, key: str, value: Any):
        """设置参数值"""
        self.params[key] = value
    
    def get_runtime_data(self, key: str, default: Any = None) -> Any:
        """获取运行时数据"""
        return self.runtime_data.get(key, default)
    
    def set_runtime_data(self, key: str, value: Any):
        """设置运行时数据"""
        self.runtime_data[key] = value
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取策略状态信息"""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_execution_time": self.last_execution_time,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_signal": {
                "type": self.last_signal.signal_type.value if self.last_signal else None,
                "symbol": self.last_signal.symbol if self.last_signal else None,
                "quantity": self.last_signal.quantity if self.last_signal else None,
                "reason": self.last_signal.reason if self.last_signal else None
            } if self.last_signal else None
        }
    
    def start(self):
        """启动策略"""
        if self.status == StrategyStatus.INITIALIZED or self.status == StrategyStatus.PAUSED:
            self.status = StrategyStatus.RUNNING
    
    def pause(self):
        """暂停策略"""
        if self.status == StrategyStatus.RUNNING:
            self.status = StrategyStatus.PAUSED
    
    def stop(self):
        """停止策略"""
        self.status = StrategyStatus.STOPPED
    
    def reset_error(self):
        """重置错误状态"""
        if self.status == StrategyStatus.ERROR:
            self.status = StrategyStatus.INITIALIZED
            self.last_error = None
    
    def _validate_config(self):
        """验证配置"""
        # 检查必需参数
        required_params = self.get_required_params()
        missing_params = [param for param in required_params if param not in self.params]
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        
        # 参数验证
        errors = self.validate_params(self.params)
        if errors:
            raise ValueError(f"Parameter validation failed: {errors}")
    
    def to_json(self) -> Dict[str, Any]:
        """转换为JSON格式"""
        return {
            "name": self.name,
            "config": self.config,
            "params": self.params,
            "metadata": self.metadata,
            "status": self.status.value,
            "runtime_data": self.runtime_data,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "last_error": self.last_error
        }
