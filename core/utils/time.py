# core/utils/time.py
# 功能：提供时间相关的工具函数
from datetime import datetime

def get_current_timestamp() -> int:
    """获取当前时间戳（秒）"""
    return int(datetime.now().timestamp())

def format_timestamp(timestamp: int) -> str:
    """将时间戳格式化为字符串"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
