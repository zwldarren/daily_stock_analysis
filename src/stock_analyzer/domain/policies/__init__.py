"""
领域策略 (Domain Policies)

封装业务规则和政策，使用Specification模式。

这些策略将交易理念显式化，便于单独测试、组合和复用。
"""

from stock_analyzer.domain.policies.trading_rules import (
    AndSpecification,
    BullishAlignmentRule,
    ChipConcentratedRule,
    HighProfitRule,
    NotSpecification,
    NotTooHighRule,
    OrSpecification,
    RuleResult,
    TradingRule,
    create_mean_reversion_strategy,
    create_strict_entry_strategy,
    create_trend_following_strategy,
)

__all__ = [
    # 基础组件
    "TradingRule",
    "RuleResult",
    # 具体规则
    "BullishAlignmentRule",
    "NotTooHighRule",
    "ChipConcentratedRule",
    "HighProfitRule",
    # 规则组合
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    # 预定义策略
    "create_strict_entry_strategy",
    "create_trend_following_strategy",
    "create_mean_reversion_strategy",
]
