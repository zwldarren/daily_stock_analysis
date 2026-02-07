"""
===================================
趋势交易分析器 - 基于用户交易理念
===================================

交易理念核心原则：
1. 严进策略 - 不追高，追求每笔交易成功率
2. 趋势交易 - MA5>MA10>MA20 多头排列，顺势而为
3. 效率优先 - 关注筹码结构好的股票
4. 买点偏好 - 在 MA5/MA10 附近回踩买入

技术标准：
- 多头排列：MA5 > MA10 > MA20
- 乖离率：(Close - MA5) / MA5 < 5%（不追高）
- 量能形态：缩量回调优先
"""

import logging

import pandas as pd

from stock_analyzer.technical.calculator import IndicatorCalculator
from stock_analyzer.technical.formatter import ResultFormatter
from stock_analyzer.technical.macd import MACDAnalyzer
from stock_analyzer.technical.result import TrendAnalysisResult
from stock_analyzer.technical.rsi import RSIAnalyzer
from stock_analyzer.technical.signal import SignalGenerator
from stock_analyzer.technical.trend import TrendAnalyzer

logger = logging.getLogger(__name__)


class StockTrendAnalyzer:
    """
    股票趋势分析器

    基于用户交易理念实现：
    1. 趋势判断 - MA5>MA10>MA20 多头排列
    2. 乖离率检测 - 不追高，偏离 MA5 超过 5% 不买
    3. 量能分析 - 偏好缩量回调
    4. 买点识别 - 回踩 MA5/MA10 支撑
    5. MACD 指标 - 趋势确认和金叉死叉信号
    6. RSI 指标 - 超买超卖判断
    """

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze(self, df: pd.DataFrame, code: str) -> TrendAnalysisResult:
        """
        分析股票趋势

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            code: 股票代码

        Returns:
            TrendAnalysisResult 分析结果
        """
        result = TrendAnalysisResult(code=code)

        if df is None or df.empty or len(df) < 20:
            logger.warning(f"{code} 数据不足，无法进行趋势分析")
            result.risk_factors.append("数据不足，无法完成分析")
            return result

        # 确保数据按日期排序
        df = df.sort_values("date").reset_index(drop=True)

        # 计算均线
        df = IndicatorCalculator.calculate_mas(df)

        # 计算 MACD 和 RSI
        df = IndicatorCalculator.calculate_macd(df)
        df = IndicatorCalculator.calculate_rsi(df)

        # 获取最新数据
        latest = df.iloc[-1]
        result.current_price = float(latest["close"])
        result.ma5 = float(latest["MA5"])
        result.ma10 = float(latest["MA10"])
        result.ma20 = float(latest["MA20"])
        result.ma60 = float(latest.get("MA60", 0))

        # 1. 趋势判断
        TrendAnalyzer.analyze_trend(df, result)

        # 2. 乖离率计算
        TrendAnalyzer.calculate_bias(result)

        # 3. 量能分析
        TrendAnalyzer.analyze_volume(df, result)

        # 4. 支撑压力分析
        TrendAnalyzer.analyze_support_resistance(df, result)

        # 5. MACD 分析
        MACDAnalyzer.analyze(df, result)

        # 6. RSI 分析
        RSIAnalyzer.analyze(df, result)

        # 7. 生成买入信号
        SignalGenerator.generate(result)

        return result

    def format_analysis(self, result: TrendAnalysisResult) -> str:
        """
        格式化分析结果为文本

        Args:
            result: 分析结果

        Returns:
            格式化的分析文本
        """
        return ResultFormatter.format(result)


if __name__ == "__main__":
    # 测试代码
    import numpy as np

    logging.basicConfig(level=logging.INFO)

    dates = pd.date_range(start="2025-01-01", periods=60, freq="D")
    np.random.seed(42)

    # 模拟多头排列的数据
    base_price = 10.0
    prices = [base_price]
    for _i in range(59):
        change = np.random.randn() * 0.02 + 0.003  # 轻微上涨趋势
        prices.append(prices[-1] * (1 + change))

    df = pd.DataFrame(
        {
            "date": dates,
            "open": prices,
            "high": [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
            "low": [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
            "close": prices,
            "volume": [np.random.randint(1000000, 5000000) for _ in prices],
        }
    )

    analyzer = StockTrendAnalyzer()
    result = analyzer.analyze(df, "000001")
    print(analyzer.format_analysis(result))
