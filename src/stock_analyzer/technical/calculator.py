"""
技术指标计算模块

提供均线、MACD、RSI等技术指标的计算
"""

import pandas as pd


class IndicatorCalculator:
    """技术指标计算器"""

    # MACD 参数（标准12/26/9）
    MACD_FAST = 12  # 快线周期
    MACD_SLOW = 26  # 慢线周期
    MACD_SIGNAL = 9  # 信号线周期

    # RSI 参数
    RSI_SHORT = 6  # 短期RSI周期
    RSI_MID = 12  # 中期RSI周期
    RSI_LONG = 24  # 长期RSI周期

    @staticmethod
    def calculate_mas(df: pd.DataFrame) -> pd.DataFrame:
        """计算均线"""
        df = df.copy()
        df["MA5"] = df["close"].rolling(window=5).mean()
        df["MA10"] = df["close"].rolling(window=10).mean()
        df["MA20"] = df["close"].rolling(window=20).mean()
        if len(df) >= 60:
            df["MA60"] = df["close"].rolling(window=60).mean()
        else:
            df["MA60"] = df["MA20"]  # 数据不足时使用 MA20 替代
        return df

    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 MACD 指标

        公式：
        - EMA(12)：12日指数移动平均
        - EMA(26)：26日指数移动平均
        - DIF = EMA(12) - EMA(26)
        - DEA = EMA(DIF, 9)
        - MACD = (DIF - DEA) * 2
        """
        df = df.copy()

        # 计算快慢线 EMA
        ema_fast = df["close"].ewm(span=IndicatorCalculator.MACD_FAST, adjust=False).mean()
        ema_slow = df["close"].ewm(span=IndicatorCalculator.MACD_SLOW, adjust=False).mean()

        # 计算快线 DIF
        df["MACD_DIF"] = ema_fast - ema_slow

        # 计算信号线 DEA
        df["MACD_DEA"] = df["MACD_DIF"].ewm(span=IndicatorCalculator.MACD_SIGNAL, adjust=False).mean()

        # 计算柱状图
        df["MACD_BAR"] = (df["MACD_DIF"] - df["MACD_DEA"]) * 2

        return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 RSI 指标

        公式：
        - RS = 平均上涨幅度 / 平均下跌幅度
        - RSI = 100 - (100 / (1 + RS))
        """
        df = df.copy()

        for period in [
            IndicatorCalculator.RSI_SHORT,
            IndicatorCalculator.RSI_MID,
            IndicatorCalculator.RSI_LONG,
        ]:
            # 计算价格变化
            delta = df["close"].diff()

            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # 计算平均涨跌幅
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            # 计算 RS 和 RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # 填充 NaN 值
            rsi = rsi.fillna(50)  # 默认中性值

            # 添加到 DataFrame
            col_name = f"RSI_{period}"
            df[col_name] = rsi

        return df
