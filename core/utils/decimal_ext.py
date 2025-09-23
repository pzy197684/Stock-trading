# core/utils/decimal_ext.py
from decimal import Decimal, ROUND_DOWN

def round_decimal(value: float, precision: int = 4) -> Decimal:
    """对浮动值进行精度控制"""
    return Decimal(value).quantize(Decimal(10) ** -precision, rounding=ROUND_DOWN)
