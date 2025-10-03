# core/utils/error_codes.py
# 功能：错误编码管理，提供中文错误信息
from typing import Dict, Optional

# HTTP状态码对应的中文说明
HTTP_STATUS_CODES = {
    400: "请求参数错误",
    401: "身份验证失败", 
    403: "访问被拒绝",
    404: "资源不存在",
    409: "资源冲突",
    500: "内部服务器错误",
    502: "网关错误",
    503: "服务不可用",
    504: "网关超时"
}

# 业务错误编码对应的中文说明
BUSINESS_ERROR_CODES = {
    "DUPLICATE_INSTANCE": "重复实例错误 - 相同的平台、账号、策略、交易对实例已存在",
    "INVALID_ACCOUNT": "无效账号 - 账号不存在或配置错误",
    "INVALID_PLATFORM": "不支持的平台 - 请使用BINANCE、COINW、OKX或DEEP",
    "INVALID_STRATEGY": "无效策略 - 策略不存在或配置错误",
    "INSUFFICIENT_BALANCE": "余额不足 - 账户余额不足以执行交易",
    "POSITION_LIMIT_EXCEEDED": "仓位限制超出 - 超出最大仓位限制",
    "RISK_LIMIT_EXCEEDED": "风险限制超出 - 超出风险控制阈值",
    "API_CONNECTION_FAILED": "API连接失败 - 无法连接到交易所API",
    "ORDER_FAILED": "订单失败 - 下单操作失败",
    "STRATEGY_NOT_RUNNING": "策略未运行 - 请先启动策略",
    "PARAMETER_VALIDATION_FAILED": "参数验证失败 - 参数不符合要求",
    "WEBSOCKET_CONNECTION_FAILED": "WebSocket连接失败 - 连接中断",
    "EMERGENCY_STOP": "紧急停止 - 触发紧急停止机制",
    "FORCE_LIQUIDATION": "强制平仓 - 系统自动强制平仓",
    "HEDGE_PROTECTION": "对冲保护 - 对冲机制触发保护",
    "FAST_ADD_PAUSED": "快速加仓暂停 - 快速加仓功能暂时停用",
    "COOLDOWN_ACTIVE": "冷却期激活 - 操作处于冷却期",
    "PARAMETERS_INCOMPLETE": "参数不完整 - 所有参数必须填写完毕且不为0",
    "INSTANCE_NOT_FOUND": "实例不存在 - 未找到指定的策略实例",
    "DELETE_INSTANCE_FAILED": "删除实例失败 - 无法删除指定实例"
}

# 解决方案提示
ERROR_SOLUTIONS = {
    "DUPLICATE_INSTANCE": "请检查是否已有相同平台、账号、策略、交易对的实例",
    "INVALID_ACCOUNT": "请检查账号配置文件是否存在且正确",
    "INVALID_PLATFORM": "请检查平台名称是否正确",
    "INVALID_STRATEGY": "请检查策略名称和配置文件",
    "INSUFFICIENT_BALANCE": "请检查账户余额并充值",
    "POSITION_LIMIT_EXCEEDED": "请调整仓位大小或风控参数",
    "RISK_LIMIT_EXCEEDED": "请调整风控参数或平仓部分头寸",
    "API_CONNECTION_FAILED": "请检查网络连接和API密钥配置",
    "ORDER_FAILED": "请检查订单参数和市场状态",
    "STRATEGY_NOT_RUNNING": "请先启动策略再执行操作",
    "PARAMETER_VALIDATION_FAILED": "请检查并修正参数值",
    "WEBSOCKET_CONNECTION_FAILED": "请检查网络连接，系统会自动重连",
    "PARAMETERS_INCOMPLETE": "请确保所有必填参数已填写且不为0",
    "INSTANCE_NOT_FOUND": "请检查实例是否存在",
    "DELETE_INSTANCE_FAILED": "请重试或联系技术支持"
}

class ErrorCodeManager:
    """错误编码管理器"""
    
    @staticmethod
    def get_chinese_message(error_code: str, default_message: str = "") -> str:
        """
        获取错误编码对应的中文说明
        
        Args:
            error_code: 错误编码
            default_message: 默认消息
            
        Returns:
            中文错误说明
        """
        # 首先检查是否是HTTP状态码
        if error_code.isdigit():
            status_code = int(error_code)
            if status_code in HTTP_STATUS_CODES:
                chinese_msg = HTTP_STATUS_CODES[status_code]
                return f"{chinese_msg}{' - ' + default_message if default_message else ''}"
        
        # 检查业务错误编码
        if error_code in BUSINESS_ERROR_CODES:
            return BUSINESS_ERROR_CODES[error_code]
        
        # 返回默认消息
        return default_message or f"未知错误编码: {error_code}"
    
    @staticmethod
    def get_solution(error_code: str) -> Optional[str]:
        """
        获取错误编码对应的解决方案
        
        Args:
            error_code: 错误编码
            
        Returns:
            解决方案说明，如果没有则返回None
        """
        return ERROR_SOLUTIONS.get(error_code)
    
    @staticmethod
    def format_error_response(error_code: str, original_message: str = "", 
                            details: Optional[Dict] = None) -> Dict:
        """
        格式化错误响应
        
        Args:
            error_code: 错误编码
            original_message: 原始错误消息
            details: 额外详情
            
        Returns:
            格式化的错误响应
        """
        chinese_message = ErrorCodeManager.get_chinese_message(error_code, original_message)
        solution = ErrorCodeManager.get_solution(error_code)
        
        response = {
            "success": False,
            "error_code": error_code,
            "message": chinese_message,
            "original_message": original_message
        }
        
        if solution:
            response["solution"] = solution
        
        if details:
            response["details"] = details
            
        return response

# 便捷函数
def get_error_message(error_code: str, default_message: str = "") -> str:
    """获取错误编码对应的中文说明"""
    return ErrorCodeManager.get_chinese_message(error_code, default_message)

def format_error(error_code: str, message: str = "", **kwargs) -> Dict:
    """格式化错误响应"""
    return ErrorCodeManager.format_error_response(error_code, message, kwargs)

# 预定义的常用错误响应
def duplicate_instance_error(platform: str, account: str, strategy: str, symbol: str) -> Dict:
    """重复实例错误"""
    return format_error(
        "DUPLICATE_INSTANCE",
        f"平台 {platform}，账户 {account}，策略 {strategy}，交易对 {symbol} 的实例已存在",
        platform=platform,
        account=account,
        strategy=strategy,
        symbol=symbol
    )

def parameters_incomplete_error() -> Dict:
    """参数不完整错误"""
    return format_error(
        "PARAMETERS_INCOMPLETE",
        "所有参数必须填写完毕且不为0才能保存"
    )

def instance_not_found_error(account: str, instance_id: str) -> Dict:
    """实例不存在错误"""
    return format_error(
        "INSTANCE_NOT_FOUND",
        f"账户 {account} 的实例 {instance_id} 不存在",
        account=account,
        instance_id=instance_id
    )
