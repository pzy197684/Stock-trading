# core/utils/decimal_ext.py
# 功能：扩展Decimal的功能，提供更方便的数值处理
from decimal import Decimal, ROUND_DOWN

# 常用常量
ZERO = Decimal('0')

def round_decimal(value: float, precision: int = 4) -> Decimal:
    """对浮动值进行精度控制"""
    return Decimal(value).quantize(Decimal(10) ** -precision, rounding=ROUND_DOWN)
