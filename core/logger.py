
# core/logger.py
# 功能：增强的日志记录功能，支持详细错误追踪和中文输出
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "runtime.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")
TRADE_LOG_FILE = os.path.join(LOG_DIR, "trade.log")

class EnhancedLogger:
    def __init__(self, log_file=LOG_FILE):
        self.logger = logging.getLogger("stock_trading")
        self.logger.setLevel(logging.INFO)  # 改为INFO级别，减少DEBUG噪音
        
        # 详细格式化器 - 包含文件名、函数名、行号
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 简化格式化器 - 用于控制台
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 控制台处理器 - 支持中文输出
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(simple_formatter)
            console_handler.setLevel(logging.WARNING)  # 控制台只显示WARNING及以上级别
            
            # 文件处理器 - 详细日志
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(logging.DEBUG)
            
            # 错误文件处理器 - 只记录错误和异常
            error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
            error_handler.setFormatter(detailed_formatter)
            error_handler.setLevel(logging.ERROR)
            
            # 交易日志处理器
            self.trade_handler = logging.FileHandler(TRADE_LOG_FILE, encoding="utf-8")
            self.trade_handler.setFormatter(detailed_formatter)
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(error_handler)

    def _get_caller_info(self, skip_frames=2):
        """获取调用者信息"""
        frame = sys._getframe(skip_frames)
        filename = os.path.basename(frame.f_code.co_filename)
        func_name = frame.f_code.co_name
        line_no = frame.f_lineno
        return f"[{filename}:{func_name}:{line_no}]"

    def debug(self, message, *args, **kwargs):
        """调试信息"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """普通信息"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """警告信息"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """错误信息"""
        self.logger.error(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        """异常信息（自动包含堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """严重错误"""
        self.logger.critical(message, *args, **kwargs)

    def trade(self, message, *args, **kwargs):
        """交易相关日志"""
        trade_logger = logging.getLogger("trade")
        if not trade_logger.handlers:
            trade_logger.addHandler(self.trade_handler)
            trade_logger.setLevel(logging.INFO)
        trade_logger.info(message, *args, **kwargs)

    # 保持向后兼容性
    def log_info(self, message):
        """兼容旧版本的info方法"""
        self.info(message)

    def log_warning(self, message):
        """兼容旧版本的warning方法"""
        self.warning(message)

    def log_error(self, message):
        """兼容旧版本的error方法"""
        self.error(message)

    def log_exception(self, message):
        """兼容旧版本的exception方法"""
        self.exception(message)

    def log_trade(self, action, symbol, side, quantity, price, order_id=None, **kwargs):
        """专门的交易日志记录"""
        trade_info = {
            'timestamp': datetime.now().isoformat(),
            'action': action,  # 'OPEN', 'CLOSE', 'CANCEL', etc.
            'symbol': symbol,
            'side': side,      # 'BUY', 'SELL'
            'quantity': quantity,
            'price': price,
            'order_id': order_id,
            **kwargs
        }
        
        trade_msg = f"🔄 {action} | {symbol} | {side} | 数量:{quantity} | 价格:{price}"
        if order_id:
            trade_msg += f" | 订单:{order_id}"
        
        for key, value in kwargs.items():
            trade_msg += f" | {key}:{value}"
            
        self.trade(trade_msg)
        self.info(trade_msg)  # 同时记录到主日志

    def log_strategy_event(self, strategy_name, event_type, message, **kwargs):
        """策略事件日志"""
        event_msg = f"📈 策略[{strategy_name}] - {event_type}: {message}"
        
        for key, value in kwargs.items():
            event_msg += f" | {key}:{value}"
            
        self.info(event_msg)

    def log_api_call(self, platform, endpoint, method='GET', status_code=None, response_time=None, error=None):
        """API调用日志"""
        if error:
            msg = f"❌ API调用失败 | {platform} | {method} {endpoint} | 错误: {error}"
            self.error(msg)
        else:
            msg = f"✅ API调用成功 | {platform} | {method} {endpoint}"
            if status_code:
                msg += f" | 状态码:{status_code}"
            if response_time:
                msg += f" | 耗时:{response_time:.2f}ms"
            self.debug(msg)

    def log_system_event(self, event_type, message, level='info', **kwargs):
        """系统事件日志"""
        event_msg = f"🖥️ 系统事件 | {event_type}: {message}"
        
        for key, value in kwargs.items():
            event_msg += f" | {key}:{value}"
        
        getattr(self, level)(event_msg)

# 实例化增强版 Logger
logger = EnhancedLogger()

# 为了向后兼容，保留原有的别名
Logger = EnhancedLogger

