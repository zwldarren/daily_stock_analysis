"""
领域值对象 (Value Objects)

值对象特点：
1. 不可变（immutable）
2. 通过属性值判断相等性
3. 没有唯一标识
4. 可以包含业务规则验证

这些值对象用于确保数据有效性，封装业务概念。
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class StockCode:
    """
    股票代码值对象

    规则：
    - A股：6位数字（如 000001, 600519）
    - 港股：4-5位数字（如 00700）
    - 美股：1-5位字母（如 AAPL）

    使用示例：
        code = StockCode("000001")  # 自动格式化
        code = StockCode.from_market("000001", "SZ")  # 带市场信息
    """

    code: str
    market: str | None = None  # "SH", "SZ", "HK", "US"

    def __post_init__(self):
        # 验证并规范化
        normalized = self._normalize(self.code)
        object.__setattr__(self, "code", normalized)

    @staticmethod
    def _normalize(code: str) -> str:
        """规范化股票代码"""
        if not code:
            raise ValueError("股票代码不能为空")

        code = code.strip().upper()

        # 移除市场前缀（如 SH600519 -> 600519）
        if code.startswith(("SH", "SZ", "BJ")) and len(code) == 8:
            code = code[2:]

        # 基础验证
        if not code.isalnum():
            raise ValueError(f"股票代码只能包含数字和字母: {code}")

        return code

    def is_a_share(self) -> bool:
        """是否为A股"""
        return len(self.code) == 6 and self.code.isdigit()

    def is_hk_stock(self) -> bool:
        """是否为港股"""
        return len(self.code) <= 5 and self.code.isdigit() and self.code.startswith("0")

    def is_us_stock(self) -> bool:
        """是否为美股"""
        return self.code.isalpha()

    def with_market_prefix(self) -> str:
        """添加市场前缀（如 000001 -> SZ000001）"""
        if self.market:
            return f"{self.market}{self.code}"

        # 自动推断市场
        if self.is_a_share():
            if self.code.startswith(("60", "68", "88", "89")):
                return f"SH{self.code}"
            else:
                return f"SZ{self.code}"
        return self.code

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"StockCode({self.code})"


@dataclass(frozen=True)
class Price:
    """
    价格值对象

    特点：
    - 使用Decimal确保精度
    - 自动保留2位小数
    - 支持价格变动计算

    使用示例：
        price = Price(10.5)
        new_price = price.change_percent(5.0)  # 上涨5%
    """

    value: Decimal

    def __init__(self, value: float | int | str | Decimal):
        if isinstance(value, Decimal):
            object.__setattr__(self, "value", value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        else:
            object.__setattr__(self, "value", Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def change_percent(self, percent: float) -> Price:
        """计算变动后的价格"""
        change = self.value * Decimal(str(percent / 100))
        return Price(self.value + change)

    def change_amount(self, amount: float) -> Price:
        """计算变动后的价格（按金额）"""
        return Price(self.value + Decimal(str(amount)))

    def difference(self, other: Price) -> Decimal:
        """计算价格差"""
        return self.value - other.value

    def percent_change(self, other: Price) -> float:
        """计算百分比变化"""
        if other.value == 0:
            return 0.0
        return float((self.value - other.value) / other.value * 100)

    def is_higher_than(self, other: Price) -> bool:
        """是否高于其他价格"""
        return self.value > other.value

    def to_float(self) -> float:
        """转换为float（用于计算）"""
        return float(self.value)

    def __str__(self) -> str:
        return f"{self.value:.2f}"

    def __repr__(self) -> str:
        return f"Price({self.value})"

    def __add__(self, other: Price) -> Price:
        return Price(self.value + other.value)

    def __sub__(self, other: Price) -> Price:
        return Price(self.value - other.value)

    def __mul__(self, multiplier: float) -> Price:
        return Price(self.value * Decimal(str(multiplier)))

    def __truediv__(self, divisor: float) -> Price:
        return Price(self.value / Decimal(str(divisor)))


@dataclass(frozen=True)
class Volume:
    """
    成交量值对象

    特点：
    - 支持手/股单位转换
    - 格式化显示（如 10.5万手）

    使用示例：
        vol = Volume(15000)  # 15000股
        print(vol.to_hands())  # 150手
        print(vol.format())  # 1.50万
    """

    shares: int  # 股数

    def to_hands(self) -> int:
        """转换为手（1手 = 100股）"""
        return self.shares // 100

    def format(self) -> str:
        """格式化显示"""
        if self.shares >= 100_000_000:
            return f"{self.shares / 100_000_000:.2f}亿"
        elif self.shares >= 10_000:
            return f"{self.shares / 10_000:.2f}万"
        else:
            return f"{self.shares:,}"

    def __str__(self) -> str:
        return f"{self.shares:,}股"

    def __repr__(self) -> str:
        return f"Volume({self.shares})"

    def __add__(self, other: Volume) -> Volume:
        return Volume(self.shares + other.shares)


@dataclass(frozen=True)
class DateRange:
    """
    日期范围值对象

    用于表示数据查询的时间范围。

    使用示例：
        range = DateRange.days(30)  # 最近30天
        range = DateRange("2024-01-01", "2024-01-31")  # 指定范围
    """

    start: str  # YYYY-MM-DD
    end: str  # YYYY-MM-DD

    @classmethod
    def days(cls, n: int) -> DateRange:
        """创建最近N天的范围"""
        from datetime import datetime, timedelta

        end = datetime.now()
        start = end - timedelta(days=n)
        return cls(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

    @property
    def days_count(self) -> int:
        """计算天数"""
        from datetime import datetime

        start = datetime.strptime(self.start, "%Y-%m-%d")
        end = datetime.strptime(self.end, "%Y-%m-%d")
        return (end - start).days + 1

    def contains(self, date: str) -> bool:
        """检查日期是否在范围内"""
        return self.start <= date <= self.end

    def __str__(self) -> str:
        return f"{self.start} ~ {self.end}"

    def __repr__(self) -> str:
        return f"DateRange({self.start}, {self.end})"


@dataclass(frozen=True)
class MovingAverage:
    """
    移动平均值对象

    封装均线数据和计算。

    使用示例：
        ma = MovingAverage(ma5=10.5, ma10=10.2, ma20=10.0)
        if ma.is_bullish_alignment():  # 多头排列
            print("趋势向上")
    """

    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None
    ma30: float | None = None
    ma60: float | None = None

    def is_bullish_alignment(self) -> bool:
        """是否为多头排列（MA5 > MA10 > MA20）"""
        return (
            self.ma5 is not None
            and self.ma10 is not None
            and self.ma20 is not None
            and self.ma5 > self.ma10 > self.ma20
        )

    def is_bearish_alignment(self) -> bool:
        """是否为空头排列（MA5 < MA10 < MA20）"""
        return (
            self.ma5 is not None
            and self.ma10 is not None
            and self.ma20 is not None
            and self.ma5 < self.ma10 < self.ma20
        )

    def deviation_from_ma5(self, price: float) -> float:
        """计算相对于MA5的乖离率（%）"""
        if self.ma5 is None or self.ma5 == 0:
            return 0.0
        return (price - self.ma5) / self.ma5 * 100

    def nearest_support(self, price: float) -> tuple[str, float] | None:
        """找到最近的支撑位（均线）"""
        mas = [("MA5", self.ma5), ("MA10", self.ma10), ("MA20", self.ma20)]
        mas = [(name, val) for name, val in mas if val is not None and val < price]

        if not mas:
            return None

        return min(mas, key=lambda x: price - x[1])

    def __str__(self) -> str:
        parts = []
        if self.ma5:
            parts.append(f"MA5={self.ma5:.2f}")
        if self.ma10:
            parts.append(f"MA10={self.ma10:.2f}")
        if self.ma20:
            parts.append(f"MA20={self.ma20:.2f}")
        return ", ".join(parts)


@dataclass(frozen=True)
class BiasRate:
    """
    乖离率值对象

    乖离率 = (价格 - 均线) / 均线 * 100

    使用示例：
        bias = BiasRate.from_price_and_ma(10.5, 10.0)  # 5%乖离
        if bias.is_overbought():  # 超买
            print("不宜追高")
    """

    value: float  # 百分比值
    price: float
    ma_value: float
    ma_type: str  # "MA5", "MA10", etc.

    @classmethod
    def from_price_and_ma(cls, price: float, ma: float, ma_type: str = "MA") -> BiasRate:
        """从价格和均线计算乖离率"""
        value = 0.0 if ma == 0 else (price - ma) / ma * 100
        return cls(value=value, price=price, ma_value=ma, ma_type=ma_type)

    def is_overbought(self, threshold: float = 5.0) -> bool:
        """是否超买（乖离率过高）"""
        return self.value > threshold

    def is_oversold(self, threshold: float = -5.0) -> bool:
        """是否超卖（乖离率过低）"""
        return self.value < threshold

    def is_at_support(self, tolerance: float = 2.0) -> bool:
        """是否在支撑位附近（回踩均线）"""
        return abs(self.value) <= tolerance and self.value <= 0

    def __str__(self) -> str:
        return f"{self.value:+.2f}%"

    def __repr__(self) -> str:
        return f"BiasRate({self.value:.2f}%)"


@dataclass(frozen=True)
class ChipDistribution:
    """
    筹码分布值对象

    封装筹码集中度、获利比例等指标。

    使用示例：
        chip = ChipDistribution(profit_ratio=0.75, concentration_90=15.0)
        if chip.is_concentrated():
            print("筹码集中，关注突破")
    """

    profit_ratio: float  # 获利比例 (0-1)
    avg_cost: float | None = None  # 平均成本
    concentration_90: float | None = None  # 90%筹码集中度
    concentration_70: float | None = None  # 70%筹码集中度

    def is_concentrated(self, threshold: float = 20.0) -> bool:
        """筹码是否集中"""
        if self.concentration_90 is None:
            return False
        return self.concentration_90 < threshold

    def is_distributed(self, threshold: float = 40.0) -> bool:
        """筹码是否分散"""
        if self.concentration_90 is None:
            return False
        return self.concentration_90 > threshold

    def profit_percent(self) -> float:
        """获利比例百分比"""
        return self.profit_ratio * 100

    def is_high_profit(self, threshold: float = 80.0) -> bool:
        """是否高获利盘"""
        return self.profit_percent() > threshold

    def __str__(self) -> str:
        return f"获利={self.profit_percent():.1f}%, 集中度90={self.concentration_90 or 'N/A'}"


@dataclass(frozen=True)
class TurnoverRate:
    """
    换手率值对象

    使用示例：
        turnover = TurnoverRate(5.5)  # 5.5%
        if turnover.is_active():
            print("交易活跃")
    """

    value: float  # 百分比

    def is_active(self, threshold: float = 3.0) -> bool:
        """是否活跃（高换手）"""
        return self.value > threshold

    def is_low(self, threshold: float = 1.0) -> bool:
        """是否低换手"""
        return self.value < threshold

    def __str__(self) -> str:
        return f"{self.value:.2f}%"

    def __repr__(self) -> str:
        return f"TurnoverRate({self.value:.2f}%)"
