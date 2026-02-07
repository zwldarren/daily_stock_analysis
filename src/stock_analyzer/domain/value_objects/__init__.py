"""
值对象

值对象是DDD中无身份标识的对象，通过属性值相等性判断。
本模块包含价格、涨跌幅、时间范围等值对象。
"""

from dataclasses import dataclass
from decimal import Decimal

from stock_analyzer.domain.value_objects.stock_vo import (
    BiasRate,
    ChipDistribution,
    DateRange,
    MovingAverage,
    Price,
    StockCode,
    TurnoverRate,
    Volume,
)


@dataclass(frozen=True)
class Percentage:
    """
    百分比值对象

    表示百分比数值，用于涨跌幅、成交量比等场景。

    示例：
        pct = Percentage(Decimal("5.5"))  # 5.5%
        str(pct)  # "5.50%"
    """

    value: Decimal

    def __post_init__(self) -> None:
        """初始化后验证"""
        # 百分比值可以超过100%或小于0
        pass

    def is_positive(self) -> bool:
        """是否为正数"""
        return self.value > 0

    def is_negative(self) -> bool:
        """是否为负数"""
        return self.value < 0

    def abs(self) -> Percentage:
        """返回绝对值"""
        return Percentage(abs(self.value))

    def __str__(self) -> str:
        sign = "+" if self.value > 0 else ""
        return f"{sign}{self.value:.2f}%"

    def __float__(self) -> float:
        return float(self.value)


__all__ = [
    # 原有值对象
    "Percentage",
    # 新增股票领域值对象
    "StockCode",
    "Price",
    "Volume",
    "DateRange",
    "MovingAverage",
    "BiasRate",
    "ChipDistribution",
    "TurnoverRate",
]
