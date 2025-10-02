# core/websocket_logger.py
# 功能：WebSocket日志推送功能，支持实时日志传输
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable


class WebSocketLogHandler(logging.Handler):
    """WebSocket日志处理器"""
    
    def __init__(self):
        super().__init__()
        self.websocket_broadcast_func: Optional[Callable] = None
        
    def set_broadcast_func(self, func: Callable):
        """设置WebSocket广播函数"""
        self.websocket_broadcast_func = func
        
    def emit(self, record):
        """发送日志记录到WebSocket"""
        if not self.websocket_broadcast_func:
            return
            
        try:
            # 格式化日志记录
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname.lower(),
                "message": self.format(record),
                "source": record.name,
                "category": getattr(record, 'category', 'system'),
                "data": getattr(record, 'data', {}),
                "file": record.filename,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # 异步发送到WebSocket
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.websocket_broadcast_func(log_entry))
                else:
                    # 如果当前线程没有事件循环，创建一个临时的任务
                    asyncio.run_coroutine_threadsafe(
                        self.websocket_broadcast_func(log_entry),
                        loop
                    )
            except Exception:
                # 如果无法获取事件循环，则忽略WebSocket推送
                pass
                
        except Exception as e:
            # 避免日志错误影响主程序
            print(f"WebSocket日志推送失败: {e}")


def setup_websocket_logging(logger_instance, broadcast_func: Callable):
    """为logger实例设置WebSocket推送功能"""
    websocket_handler = WebSocketLogHandler()
    websocket_handler.set_broadcast_func(broadcast_func)
    
    # 设置简单格式，因为详细信息已在log_entry中
    formatter = logging.Formatter('%(message)s')
    websocket_handler.setFormatter(formatter)
    
    # 添加到logger
    logger_instance.logger.addHandler(websocket_handler)
    
    return websocket_handler


# 全局WebSocket处理器实例
_websocket_handler = None


def get_websocket_handler():
    """获取全局WebSocket处理器"""
    return _websocket_handler


def set_global_websocket_handler(handler):
    """设置全局WebSocket处理器"""
    global _websocket_handler
    _websocket_handler = handler