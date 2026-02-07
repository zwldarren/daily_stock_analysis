"""
单元测试 - 数据源基础模块

测试范围:
- DataFetchError 异常类
- BaseFetcher 抽象基类
- DataFetcherManager 管理器
- 标准化列定义

@author: Kilo Code
"""

from unittest.mock import patch

import pandas as pd
import pytest

from stock_analyzer.domain.exceptions import (
    DataFetchError,
    DataSourceUnavailableError,
    RateLimitError,
)
from stock_analyzer.infrastructure.external.data_sources.fetchers.base import (
    STANDARD_COLUMNS,
    BaseFetcher,
    DataFetcherManager,
)


# =============================================================================
# DataFetchError 异常测试
# =============================================================================
class TestDataFetchError:
    """测试数据获取异常类"""

    def test_data_fetch_error_basic(self) -> None:
        """测试基本异常抛出"""
        with pytest.raises(DataFetchError, match="测试错误"):
            raise DataFetchError("测试错误")

    def test_data_fetch_error_with_cause(self) -> None:
        """测试异常链"""
        original = ValueError("原始错误")
        with pytest.raises(DataFetchError) as exc_info:
            raise DataFetchError("包装错误") from original
        assert exc_info.value.__cause__ == original


class TestRateLimitError:
    """测试速率限制异常类"""

    def test_rate_limit_error_is_data_fetch_error(self) -> None:
        """测试 RateLimitError 是 DataFetchError 的子类"""
        assert issubclass(RateLimitError, DataFetchError)

    def test_rate_limit_error_raise(self) -> None:
        """测试抛出速率限制异常"""
        with pytest.raises(RateLimitError, match="API 限流"):
            raise RateLimitError("API 限流，请稍后重试")


class TestDataSourceUnavailableError:
    """测试数据源不可用异常类"""

    def test_data_source_unavailable_is_data_fetch_error(self) -> None:
        """测试 DataSourceUnavailableError 是 DataFetchError 的子类"""
        assert issubclass(DataSourceUnavailableError, DataFetchError)

    def test_data_source_unavailable_raise(self) -> None:
        """测试抛出数据源不可用异常"""
        with pytest.raises(DataSourceUnavailableError, match="数据源离线"):
            raise DataSourceUnavailableError("数据源离线")


# =============================================================================
# STANDARD_COLUMNS 常量测试
# =============================================================================
class TestStandardColumns:
    """测试标准化列名定义"""

    def test_standard_columns_exists(self) -> None:
        """测试 STANDARD_COLUMNS 常量存在"""
        assert isinstance(STANDARD_COLUMNS, list)

    def test_standard_columns_content(self) -> None:
        """测试 STANDARD_COLUMNS 包含预期列名"""
        expected = ["date", "open", "high", "low", "close", "volume", "amount", "pct_chg"]
        assert expected == STANDARD_COLUMNS

    def test_standard_columns_immutable(self) -> None:
        """测试 STANDARD_COLUMNS 不应被意外修改（浅测试）"""
        # 确保基本完整性
        assert "date" in STANDARD_COLUMNS
        assert "close" in STANDARD_COLUMNS


# =============================================================================
# BaseFetcher 抽象基类测试
# =============================================================================
class ConcreteFetcher(BaseFetcher):
    """用于测试的具体 Fetcher 实现"""

    name = "ConcreteFetcher"
    priority = 10

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """模拟获取原始数据"""
        # 创建模拟数据
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        data = {
            "trade_date": dates.strftime("%Y-%m-%d"),
            "open": [100.0] * len(dates),
            "high": [101.0] * len(dates),
            "low": [99.0] * len(dates),
            "close": [100.5] * len(dates),
            "vol": [10000] * len(dates),
            "amount": [1000000] * len(dates),
            "pct_change": [0.5] * len(dates),
        }
        return pd.DataFrame(data)

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化列名"""
        column_mapping = {
            "trade_date": "date",
            "vol": "volume",
            "pct_change": "pct_chg",
        }
        df = df.rename(columns=column_mapping)
        return df


class TestBaseFetcher:
    """测试 BaseFetcher 抽象基类"""

    def test_base_fetcher_is_abstract(self) -> None:
        """测试 BaseFetcher 是抽象类，不能直接实例化"""
        with pytest.raises(TypeError):
            BaseFetcher()

    def test_base_fetcher_name_and_priority(self) -> None:
        """测试 name 和 priority 属性"""
        fetcher = ConcreteFetcher()
        assert fetcher.name == "ConcreteFetcher"
        assert fetcher.priority == 10

    def test_get_daily_data_success(self) -> None:
        """测试成功获取日线数据"""
        fetcher = ConcreteFetcher()
        df = fetcher.get_daily_data("600519", "2024-01-01", "2024-01-10")

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        # 验证标准化列名存在
        assert "date" in df.columns
        assert "open" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_get_daily_data_no_indicators(self) -> None:
        """测试获取数据不包含技术指标（由 IndicatorService 计算）"""
        fetcher = ConcreteFetcher()
        df = fetcher.get_daily_data("600519", days=30)

        # BaseFetcher 不再计算技术指标，这些应该由 IndicatorService 处理
        assert "ma5" not in df.columns
        assert "ma10" not in df.columns
        assert "volume_ratio" not in df.columns

    def test_get_daily_data_empty_result(self) -> None:
        """测试获取空数据时抛出异常"""

        class EmptyFetcher(BaseFetcher):
            name = "EmptyFetcher"

            def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
                return pd.DataFrame()

            def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
                return df

        fetcher = EmptyFetcher()
        with pytest.raises(DataFetchError, match="未获取到"):
            fetcher.get_daily_data("600519", "2024-01-01", "2024-01-10")


# =============================================================================
# DataFetcherManager 测试
# =============================================================================
class TestDataFetcherManager:
    """测试 DataFetcherManager 数据源管理器"""

    def test_manager_initialization_empty(self) -> None:
        """测试空管理器初始化"""
        with patch.object(DataFetcherManager, "_init_default_fetchers"):
            manager = DataFetcherManager(fetchers=[])
            assert manager._fetchers == []

    def test_manager_initialization_with_fetchers(self) -> None:
        """测试带 Fetcher 列表的管理器初始化"""
        fetcher1 = ConcreteFetcher()
        fetcher1.priority = 5

        fetcher2 = ConcreteFetcher()
        fetcher2.name = "Fetcher2"
        fetcher2.priority = 1

        manager = DataFetcherManager(fetchers=[fetcher1, fetcher2])

        # 验证按优先级排序
        assert manager._fetchers[0].name == "Fetcher2"  # priority 1
        assert manager._fetchers[1].name == "ConcreteFetcher"  # priority 5

    def test_add_fetcher(self) -> None:
        """测试添加 Fetcher"""
        fetcher1 = ConcreteFetcher()
        fetcher1.priority = 5

        manager = DataFetcherManager(fetchers=[fetcher1])

        fetcher2 = ConcreteFetcher()
        fetcher2.name = "NewFetcher"
        fetcher2.priority = 1

        manager.add_fetcher(fetcher2)

        # 验证已添加并排序
        assert len(manager._fetchers) == 2
        assert manager._fetchers[0].name == "NewFetcher"

    def test_available_fetchers_property(self) -> None:
        """测试 available_fetchers 属性"""
        fetcher1 = ConcreteFetcher()
        fetcher2 = ConcreteFetcher()
        fetcher2.name = "Fetcher2"

        manager = DataFetcherManager(fetchers=[fetcher1, fetcher2])

        names = manager.available_fetchers
        assert "ConcreteFetcher" in names
        assert "Fetcher2" in names
        assert len(names) == 2

    def test_get_daily_data_success(self) -> None:
        """测试管理器获取日线数据成功"""
        fetcher = ConcreteFetcher()

        with patch.object(ConcreteFetcher, "_fetch_raw_data") as mock_fetch:
            mock_fetch.return_value = pd.DataFrame(
                {
                    "trade_date": ["2024-01-01", "2024-01-02"],
                    "open": [100.0, 101.0],
                    "high": [101.0, 102.0],
                    "low": [99.0, 100.0],
                    "close": [100.5, 101.5],
                    "vol": [10000, 11000],
                    "amount": [1000000, 1100000],
                    "pct_change": [0.5, 1.0],
                }
            )

            manager = DataFetcherManager(fetchers=[fetcher])
            df, source = manager.get_daily_data("600519", "2024-01-01", "2024-01-02")

            assert isinstance(df, pd.DataFrame)
            assert not df.empty
            assert source == "ConcreteFetcher"

    def test_get_daily_data_failover(self) -> None:
        """测试管理器故障切换"""
        fetcher1 = ConcreteFetcher()
        fetcher1.name = "FailingFetcher"

        fetcher2 = ConcreteFetcher()
        fetcher2.name = "SuccessFetcher"

        manager = DataFetcherManager(fetchers=[fetcher1, fetcher2])

        with (
            patch.object(fetcher1, "get_daily_data", side_effect=Exception("Connection failed")),
            patch.object(fetcher2, "get_daily_data") as mock_success,
        ):
            # Mock the second fetcher to return valid data
            mock_success.return_value = pd.DataFrame(
                {
                    "date": ["2024-01-01"],
                    "open": [100.0],
                    "high": [101.0],
                    "low": [99.0],
                    "close": [100.5],
                    "volume": [10000],
                    "amount": [1000000],
                    "pct_chg": [0.5],
                }
            )

            df, source = manager.get_daily_data("600519", "2024-01-01", "2024-01-02")

            assert isinstance(df, pd.DataFrame)
            assert source == "SuccessFetcher"

    def test_get_daily_data_all_fail(self) -> None:
        """测试所有数据源都失败时抛出异常"""
        fetcher = ConcreteFetcher()

        manager = DataFetcherManager(fetchers=[fetcher])

        with (
            patch.object(fetcher, "get_daily_data", side_effect=Exception("Connection failed")),
            pytest.raises(DataFetchError, match="所有数据源"),
        ):
            manager.get_daily_data("600519", "2024-01-01", "2024-01-02")


# =============================================================================
# 辅助功能测试
# =============================================================================
class TestHelperFunctions:
    """测试辅助功能"""

    def test_base_fetcher_subclasses_must_implement(self) -> None:
        """测试子类必须实现抽象方法"""

        class IncompleteFetcher(BaseFetcher):
            name = "Incomplete"

            # 缺少 _fetch_raw_data 和 _normalize_data 实现

        with pytest.raises(TypeError):
            IncompleteFetcher()
