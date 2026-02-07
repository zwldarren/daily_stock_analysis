"""
交易策略规则 (Trading Strategy Rules)

使用Specification模式封装交易策略规则。
这些规则将交易理念显式化，便于单独测试和组合使用。

交易理念：
1. 严进策略：不追高，乖离率 > 5% 不买入
2. 趋势交易：只做MA5>MA10>MA20多头排列
3. 效率优先：关注筹码集中度好的股票
4. 买点偏好：缩量回踩MA5/MA10支撑

使用示例：
    # 单个规则
    rule = BullishAlignmentRule()
    if rule.is_satisfied_by(context):
        print("多头排列，符合买入条件")

    # 组合规则（AND）
    composite = AndSpecification([
        BullishAlignmentRule(),
        NotTooHighRule(max_bias=5.0),
        ChipConcentratedRule(threshold=20.0)
    ])
    result = composite.is_satisfied_by(context)

    # 评估并获取详情
    result = composite.evaluate(context)
    print(f"评分: {result.score}, 原因: {result.reasons}")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from stock_analyzer.domain.value_objects import (
    BiasRate,
    ChipDistribution,
    MovingAverage,
    Price,
)


@dataclass
class RuleResult:
    """规则评估结果"""

    is_satisfied: bool
    score: int  # 评分贡献（可为负）
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class TradingRule(ABC):
    """
    交易规则基类

    所有交易策略规则都继承此类。
    """

    @abstractmethod
    def is_satisfied_by(self, context: Any) -> bool:
        """
        检查上下文是否满足规则

        Args:
            context: 分析上下文（通常是AnalysisContext）

        Returns:
            是否满足规则
        """
        pass

    @abstractmethod
    def evaluate(self, context: Any) -> RuleResult:
        """
        详细评估规则

        返回包含评分、原因的详细结果。
        """
        pass


class BullishAlignmentRule(TradingRule):
    """
    多头排列规则

    规则：MA5 > MA10 > MA20
    """

    def is_satisfied_by(self, context: Any) -> bool:
        ma = self._get_ma(context)
        if not ma:
            return False
        return ma.is_bullish_alignment()

    def evaluate(self, context: Any) -> RuleResult:
        ma = self._get_ma(context)
        if not ma:
            return RuleResult(is_satisfied=False, score=0, warnings=["缺少均线数据"])

        if ma.is_bullish_alignment():
            return RuleResult(is_satisfied=True, score=20, reasons=["多头排列：MA5 > MA10 > MA20"])
        elif ma.is_bearish_alignment():
            return RuleResult(is_satisfied=False, score=-15, warnings=["空头排列，趋势向下"])
        else:
            return RuleResult(is_satisfied=False, score=-5, warnings=["均线纠缠，趋势不明"])

    def _get_ma(self, context: Any) -> MovingAverage | None:
        """从上下文中提取均线数据"""
        if hasattr(context, "daily_data") and context.daily_data:
            latest = context.daily_data[-1]
            return MovingAverage(
                ma5=latest.get("ma5"),
                ma10=latest.get("ma10"),
                ma20=latest.get("ma20"),
            )
        return None


class NotTooHighRule(TradingRule):
    """
    不追高规则（严进策略）

    规则：乖离率 > max_bias 时不买入
    """

    def __init__(self, max_bias: float = 5.0) -> None:
        self.max_bias = max_bias

    def is_satisfied_by(self, context: Any) -> bool:
        bias = self._get_bias(context)
        if bias is None:
            return True  # 没有数据，默认允许
        return not bias.is_overbought(self.max_bias)

    def evaluate(self, context: Any) -> RuleResult:
        bias = self._get_bias(context)
        if bias is None:
            return RuleResult(is_satisfied=True, score=0, warnings=["缺少乖离率数据"])

        if bias.is_overbought(self.max_bias):
            return RuleResult(
                is_satisfied=False,
                score=-30,
                warnings=[f"乖离率过高 ({bias.value:+.1f}% > {self.max_bias}%)，不宜追高"],
            )
        elif bias.value < -2:
            return RuleResult(is_satisfied=True, score=15, reasons=[f"回踩均线 ({bias.value:+.1f}%)，买入机会"])
        else:
            return RuleResult(is_satisfied=True, score=5, reasons=[f"乖离率正常 ({bias.value:+.1f}%)"])

    def _get_bias(self, context: Any) -> BiasRate | None:
        """从上下文中提取乖离率"""
        price = self._get_price(context)
        ma = self._get_ma(context)

        if price is None or ma is None or ma.ma5 is None:
            return None

        return BiasRate.from_price_and_ma(price.to_float(), ma.ma5, "MA5")

    def _get_price(self, context: Any) -> Price | None:
        """获取当前价格"""
        if hasattr(context, "realtime_quote") and context.realtime_quote:
            price_val = context.realtime_quote.get("price")
            if price_val:
                return Price(price_val)
        return None

    def _get_ma(self, context: Any) -> MovingAverage | None:
        """获取均线"""
        if hasattr(context, "daily_data") and context.daily_data:
            latest = context.daily_data[-1]
            return MovingAverage(
                ma5=latest.get("ma5"),
                ma10=latest.get("ma10"),
                ma20=latest.get("ma20"),
            )
        return None


class ChipConcentratedRule(TradingRule):
    """
    筹码集中规则（效率优先）

    规则：90%筹码集中度 < threshold 时认为集中
    """

    def __init__(self, threshold: float = 20.0) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, context: Any) -> bool:
        chip = self._get_chip(context)
        if not chip:
            return True  # 没有数据，默认允许
        return chip.is_concentrated(self.threshold)

    def evaluate(self, context: Any) -> RuleResult:
        chip = self._get_chip(context)
        if not chip:
            return RuleResult(is_satisfied=True, score=0, warnings=["缺少筹码数据"])

        if chip.is_concentrated(self.threshold):
            return RuleResult(
                is_satisfied=True,
                score=10,
                reasons=[f"筹码集中 (集中度90={chip.concentration_90:.1f}% < {self.threshold}%)"],
            )
        else:
            return RuleResult(
                is_satisfied=False, score=-5, warnings=[f"筹码分散 (集中度90={chip.concentration_90:.1f}%)"]
            )

    def _get_chip(self, context: Any) -> ChipDistribution | None:
        """从上下文中提取筹码数据"""
        if hasattr(context, "chip_data") and context.chip_data:
            data = context.chip_data
            return ChipDistribution(
                profit_ratio=data.get("profit_ratio", 0),
                avg_cost=data.get("avg_cost"),
                concentration_90=data.get("concentration_90"),
            )
        return None


class HighProfitRule(TradingRule):
    """
    高获利盘规则

    规则：获利比例 > threshold 时认为筹码稳定
    """

    def __init__(self, threshold: float = 70.0) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, context: Any) -> bool:
        chip = self._get_chip(context)
        if not chip:
            return True
        return chip.profit_percent() > self.threshold

    def evaluate(self, context: Any) -> RuleResult:
        chip = self._get_chip(context)
        if not chip:
            return RuleResult(is_satisfied=True, score=0)

        profit_pct = chip.profit_percent()
        if profit_pct > self.threshold:
            return RuleResult(
                is_satisfied=True, score=8, reasons=[f"高获利盘 ({profit_pct:.1f}% > {self.threshold}%)，筹码稳定"]
            )
        else:
            return RuleResult(
                is_satisfied=False, score=-3, warnings=[f"获利盘较低 ({profit_pct:.1f}%)", "可能还有套牢盘"]
            )

    def _get_chip(self, context: Any) -> ChipDistribution | None:
        """从上下文中提取筹码数据"""
        if hasattr(context, "chip_data") and context.chip_data:
            data = context.chip_data
            return ChipDistribution(
                profit_ratio=data.get("profit_ratio", 0),
            )
        return None


# ========== 规则组合 ==========


class AndSpecification(TradingRule):
    """
    AND组合规则

    所有子规则都必须满足
    """

    def __init__(self, rules: list[TradingRule]) -> None:
        self.rules = rules

    def is_satisfied_by(self, context: Any) -> bool:
        return all(rule.is_satisfied_by(context) for rule in self.rules)

    def evaluate(self, context: Any) -> RuleResult:
        total_score = 0
        all_reasons = []
        all_warnings = []
        all_satisfied = True

        for rule in self.rules:
            result = rule.evaluate(context)
            total_score += result.score
            all_reasons.extend(result.reasons)
            all_warnings.extend(result.warnings)
            if not result.is_satisfied:
                all_satisfied = False

        # 确保分数在合理范围
        total_score = max(0, min(100, total_score + 50))

        return RuleResult(is_satisfied=all_satisfied, score=total_score, reasons=all_reasons, warnings=all_warnings)


class OrSpecification(TradingRule):
    """
    OR组合规则

    任一子规则满足即可
    """

    def __init__(self, rules: list[TradingRule]) -> None:
        self.rules = rules

    def is_satisfied_by(self, context: Any) -> bool:
        return any(rule.is_satisfied_by(context) for rule in self.rules)

    def evaluate(self, context: Any) -> RuleResult:
        results = [rule.evaluate(context) for rule in self.rules]

        # OR规则中，任一满足即为满足
        any_satisfied = any(r.is_satisfied for r in results)

        # 分数取最高
        max_score = max(r.score for r in results)

        # 收集所有原因和警告
        all_reasons = []
        all_warnings = []
        for r in results:
            all_reasons.extend(r.reasons)
            all_warnings.extend(r.warnings)

        return RuleResult(is_satisfied=any_satisfied, score=max_score, reasons=all_reasons, warnings=all_warnings)


class NotSpecification(TradingRule):
    """
    NOT规则

    取反规则
    """

    def __init__(self, rule: TradingRule) -> None:
        self.rule = rule

    def is_satisfied_by(self, context: Any) -> bool:
        return not self.rule.is_satisfied_by(context)

    def evaluate(self, context: Any) -> RuleResult:
        result = self.rule.evaluate(context)
        return RuleResult(
            is_satisfied=not result.is_satisfied,
            score=-result.score,  # 分数取反
            reasons=result.warnings,  # 原因和警告互换
            warnings=result.reasons,
        )


# ========== 预定义策略 ==========


def create_strict_entry_strategy() -> TradingRule:
    """
    创建严进策略

    组合规则：
    1. 多头排列
    2. 不追高（乖离率<5%）
    3. 筹码集中
    4. 高获利盘
    """
    return AndSpecification(
        [
            BullishAlignmentRule(),
            NotTooHighRule(max_bias=5.0),
            ChipConcentratedRule(threshold=20.0),
            HighProfitRule(threshold=70.0),
        ]
    )


def create_trend_following_strategy() -> TradingRule:
    """
    创建趋势跟踪策略

    组合规则：
    1. 多头排列（核心规则）
    2. 乖离率不能太高
    """
    return AndSpecification(
        [
            BullishAlignmentRule(),
            NotTooHighRule(max_bias=8.0),  # 比严进策略宽松
        ]
    )


def create_mean_reversion_strategy() -> TradingRule:
    """
    创建均值回归策略

    组合规则：
    1. 乖离率过低（超卖）
    2. 但仍在多头趋势中
    """
    # 使用Not规则实现"超卖"概念
    # 即：Not(NotTooHighRule) 表示价格低于均线
    return AndSpecification(
        [
            BullishAlignmentRule(),
            NotSpecification(NotTooHighRule(max_bias=-2.0)),  # 乖离率<-2%
        ]
    )
