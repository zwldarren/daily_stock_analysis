"""
集成测试 - 数据源真实连接测试

这些测试需要真实调用上游数据源，默认情况下会被跳过。
运行方式:
    pytest tests/integration/test_data_providers_live.py -v --run-live

注意事项:
    - 这些测试会消耗 API 配额
    - 可能因网络或上游服务问题而失败
    - 不要频繁运行，避免被封禁
"""

import pandas as pd
import pytest

from stock_analyzer.domain.exceptions import DataFetchError
from stock_analyzer.domain.services.data_service import DataService
from stock_analyzer.infrastructure.external.data_sources import (
    AkshareFetcher,
    DataFetcherManager,
    EfinanceFetcher,
)
from stock_analyzer.infrastructure.external.data_sources.fetchers.realtime_types import (
    ChipDistribution,
    UnifiedRealtimeQuote,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_stock_code():
    """测试股票代码 - 贵州茅台"""
    return "600519"


@pytest.fixture
def test_etf_code():
    """测试 ETF 代码 - 有色龙头 ETF"""
    return "512400"


@pytest.fixture
def test_hk_code():
    """测试港股代码 - 腾讯控股"""
    return "00700"


@pytest.fixture
def test_us_code():
    """测试美股代码 - 苹果公司"""
    return "AAPL"


# =============================================================================
# Live Data Provider Tests
# =============================================================================


@pytest.mark.live
class TestEfinanceFetcherLive:
    """EfinanceFetcher 真实 API 测试"""

    def test_get_daily_data_stock(self, test_stock_code):
        """测试获取 A 股日线数据"""
        fetcher = EfinanceFetcher()
        df = fetcher.get_daily_data(test_stock_code, days=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) >= 1
        # 验证标准列名
        assert "date" in df.columns
        assert "open" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns
        assert df.iloc[-1]["code"] == test_stock_code

    def test_get_daily_data_etf(self, test_etf_code):
        """测试获取 ETF 日线数据"""
        fetcher = EfinanceFetcher()
        df = fetcher.get_daily_data(test_etf_code, days=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "close" in df.columns

    def test_get_realtime_quote_stock(self, test_stock_code):
        """测试获取 A 股实时行情"""
        fetcher = EfinanceFetcher()
        quote = fetcher.get_realtime_quote(test_stock_code)

        if quote is not None:
            assert isinstance(quote, UnifiedRealtimeQuote)
            assert quote.code == test_stock_code
            assert quote.price is not None
            assert quote.name is not None

    def test_get_realtime_quote_etf(self, test_etf_code):
        """测试获取 ETF 实时行情"""
        fetcher = EfinanceFetcher()
        quote = fetcher.get_realtime_quote(test_etf_code)

        if quote is not None:
            assert isinstance(quote, UnifiedRealtimeQuote)
            assert quote.code == test_etf_code

    def test_get_main_indices(self):
        """测试获取主要指数"""
        fetcher = EfinanceFetcher()
        indices = fetcher.get_main_indices()

        if indices is not None:
            assert isinstance(indices, list)
            assert len(indices) > 0
            assert "code" in indices[0]
            assert "name" in indices[0]
            assert "current" in indices[0]

    def test_get_market_stats(self):
        """测试获取市场统计"""
        fetcher = EfinanceFetcher()
        stats = fetcher.get_market_stats()

        if stats is not None:
            assert isinstance(stats, dict)
            assert "up_count" in stats
            assert "down_count" in stats

    def test_get_base_info(self, test_stock_code):
        """测试获取股票基本信息"""
        fetcher = EfinanceFetcher()
        info = fetcher.get_base_info(test_stock_code)

        if info is not None:
            assert isinstance(info, dict)
            # 基本信息通常包含市盈率、市净率等
            assert len(info) > 0


@pytest.mark.live
class TestAkshareFetcherLive:
    """AkshareFetcher 真实 API 测试"""

    def test_get_daily_data_stock(self, test_stock_code):
        """测试获取 A 股日线数据"""
        fetcher = AkshareFetcher()
        df = fetcher.get_daily_data(test_stock_code, days=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "date" in df.columns
        assert "close" in df.columns
        assert df.iloc[-1]["code"] == test_stock_code

    def test_get_daily_data_etf(self, test_etf_code):
        """测试获取 ETF 日线数据"""
        fetcher = AkshareFetcher()
        df = fetcher.get_daily_data(test_etf_code, days=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_get_daily_data_hk(self, test_hk_code):
        """测试获取港股日线数据"""
        fetcher = AkshareFetcher()
        df = fetcher.get_daily_data(test_hk_code, days=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_get_daily_data_us(self, test_us_code):
        """测试获取美股日线数据"""
        fetcher = AkshareFetcher()
        df = fetcher.get_daily_data(test_us_code, days=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_get_realtime_quote_stock(self, test_stock_code):
        """测试获取 A 股实时行情"""
        fetcher = AkshareFetcher()
        quote = fetcher.get_realtime_quote(test_stock_code)

        if quote is not None:
            assert isinstance(quote, UnifiedRealtimeQuote)
            assert quote.code == test_stock_code
            assert quote.price is not None

    def test_get_realtime_quote_etf(self, test_etf_code):
        """测试获取 ETF 实时行情"""
        fetcher = AkshareFetcher()
        quote = fetcher.get_realtime_quote(test_etf_code)

        if quote is not None:
            assert isinstance(quote, UnifiedRealtimeQuote)

    def test_get_realtime_quote_hk(self, test_hk_code):
        """测试获取港股实时行情"""
        fetcher = AkshareFetcher()
        quote = fetcher.get_realtime_quote(test_hk_code)

        if quote is not None:
            assert isinstance(quote, UnifiedRealtimeQuote)

    def test_get_chip_distribution(self, test_stock_code):
        """测试获取筹码分布数据"""
        fetcher = AkshareFetcher()
        chip = fetcher.get_chip_distribution(test_stock_code)

        if chip is not None:
            assert isinstance(chip, ChipDistribution)
            assert chip.code == test_stock_code
            assert chip.profit_ratio is not None
            assert chip.avg_cost is not None

    def test_get_stock_name(self, test_stock_code):
        """测试获取股票名称"""
        fetcher = AkshareFetcher()
        name = fetcher.get_stock_name(test_stock_code)

        if name is not None:
            assert isinstance(name, str)
            assert len(name) > 0
            # 600519 应该是贵州茅台
            assert "茅台" in name or "贵州" in name

    def test_get_stock_list(self):
        """测试获取股票列表"""
        fetcher = AkshareFetcher()
        df = fetcher.get_stock_list()

        if df is not None:
            assert isinstance(df, pd.DataFrame)
            assert not df.empty
            assert "code" in df.columns or "股票代码" in df.columns


@pytest.mark.live
class TestDataFetcherManagerLive:
    """DataFetcherManager 真实 API 测试"""

    def test_get_daily_data_with_failover(self, test_stock_code):
        """测试带故障切换的日线数据获取"""
        manager = DataFetcherManager()
        df, source = manager.get_daily_data(test_stock_code, days=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert isinstance(source, str)
        assert source in manager.available_fetchers
        assert "date" in df.columns

    def test_get_realtime_quote_with_failover(self, test_stock_code):
        """测试带故障切换的实时行情获取"""
        manager = DataFetcherManager()
        quote = manager.get_realtime_quote(test_stock_code)

        # 实时行情可能获取失败
        if quote is not None:
            assert isinstance(quote, UnifiedRealtimeQuote)
            assert quote.code == test_stock_code

    def test_batch_get_stock_names(self):
        """测试批量获取股票名称"""
        manager = DataFetcherManager()
        codes = ["600519", "000001", "000002"]
        names = manager.batch_get_stock_names(codes)

        assert isinstance(names, dict)
        # 至少应该获取到部分股票名称
        assert len(names) > 0

    def test_get_main_indices(self):
        """测试获取主要指数"""
        manager = DataFetcherManager()
        indices = manager.get_main_indices()

        assert isinstance(indices, list)
        if len(indices) > 0:
            assert "code" in indices[0]
            assert "name" in indices[0]

    def test_get_market_stats(self):
        """测试获取市场统计"""
        manager = DataFetcherManager()
        stats = manager.get_market_stats()

        assert isinstance(stats, dict)
        # 市场统计可能为空字典

    def test_get_sector_rankings(self):
        """测试获取板块排名"""
        manager = DataFetcherManager()
        top, bottom = manager.get_sector_rankings(n=3)

        assert isinstance(top, list)
        assert isinstance(bottom, list)


@pytest.mark.live
class TestDataServiceLive:
    """DataService 真实 API 测试"""

    def test_get_daily_data_from_fetcher(self, test_stock_code):
        """测试从外部数据源获取日线数据"""
        manager = DataFetcherManager()
        # DataFetcherManager 实现了 IDataFetcher 接口的所有方法
        service = DataService(fetcher_manager=manager)  # type: ignore[arg-type]

        df, source = service.get_daily_data(test_stock_code, days=5, use_cache=False)

        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert isinstance(source, str)

    def test_get_realtime_quote(self, test_stock_code):
        """测试获取实时行情"""
        manager = DataFetcherManager()
        service = DataService(fetcher_manager=manager)  # type: ignore[arg-type]

        quote = service.get_realtime_quote(test_stock_code)

        # 实时行情可能获取失败
        if quote is not None:
            assert isinstance(quote, UnifiedRealtimeQuote)

    def test_get_stock_name(self, test_stock_code):
        """测试获取股票名称"""
        manager = DataFetcherManager()
        service = DataService(fetcher_manager=manager)  # type: ignore[arg-type]

        name = service.get_stock_name(test_stock_code)

        if name is not None:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_batch_get_stock_names(self):
        """测试批量获取股票名称"""
        manager = DataFetcherManager()
        service = DataService(fetcher_manager=manager)  # type: ignore[arg-type]

        codes = ["600519", "000001", "000002"]
        names = service.batch_get_stock_names(codes)

        assert isinstance(names, dict)
        assert len(names) > 0

    def test_cache_functionality(self, test_stock_code):
        """测试缓存功能"""
        manager = DataFetcherManager()
        service = DataService(fetcher_manager=manager)  # type: ignore[arg-type]

        # 第一次获取
        name1 = service.get_stock_name(test_stock_code)

        # 第二次获取应该从缓存中读取
        name2 = service.get_stock_name(test_stock_code)

        if name1 is not None:
            assert name1 == name2

    def test_invalidate_cache(self):
        """测试缓存清除功能"""
        manager = DataFetcherManager()
        service = DataService(fetcher_manager=manager)  # type: ignore[arg-type]

        # 获取一些数据填充缓存
        service.get_stock_name("600519")

        # 清除缓存
        service.invalidate_cache()

        # 缓存被清除后应该能正常获取
        name = service.get_stock_name("600519")
        if name is not None:
            assert isinstance(name, str)


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.live
class TestDataProviderErrorHandlingLive:
    """测试数据源错误处理（真实环境）"""

    def test_invalid_stock_code(self):
        """测试无效股票代码的处理"""
        fetcher = EfinanceFetcher()

        # 使用明显无效的代码
        with pytest.raises(DataFetchError):
            fetcher.get_daily_data("INVALID999", days=5)

    def test_us_stock_in_efinance(self, test_us_code):
        """测试 Efinance 不支持美股"""
        fetcher = EfinanceFetcher()

        # Efinance 不支持美股，应该抛出异常或返回 None
        with pytest.raises(DataFetchError):
            fetcher.get_daily_data(test_us_code, days=5)

    def test_empty_data_handling(self):
        """测试空数据处理"""
        fetcher = AkshareFetcher()

        # 使用一个可能返回空数据的代码
        # 注意：这可能会因数据源而异
        try:
            df = fetcher.get_daily_data("000000", days=5)
            # 如果返回数据，应该为空 DataFrame
            assert df.empty
        except Exception:
            # 抛出异常也是可接受的
            pass


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.live
@pytest.mark.slow
class TestDataProviderPerformanceLive:
    """数据源性能测试（真实环境）"""

    def test_daily_data_response_time(self, test_stock_code):
        """测试日线数据响应时间"""
        import time

        fetcher = EfinanceFetcher()

        start = time.time()
        df = fetcher.get_daily_data(test_stock_code, days=30)
        elapsed = time.time() - start

        assert df is not None
        assert elapsed < 30  # 应该能在 30 秒内完成

    def test_realtime_quote_response_time(self, test_stock_code):
        """测试实时行情响应时间"""
        import time

        fetcher = EfinanceFetcher()

        start = time.time()
        fetcher.get_realtime_quote(test_stock_code)
        elapsed = time.time() - start

        # 实时行情可能失败，但响应时间应该合理
        assert elapsed < 10  # 应该能在 10 秒内完成

    def test_concurrent_requests(self):
        """测试并发请求性能"""
        import time

        manager = DataFetcherManager()
        codes = ["600519", "000001", "000002", "000333", "002415"]

        start = time.time()
        results = []
        for code in codes:
            try:
                df, source = manager.get_daily_data(code, days=5)
                results.append((code, df is not None))
            except Exception:
                results.append((code, False))

        elapsed = time.time() - start

        # 大部分请求应该成功
        success_count = sum(1 for _, success in results if success)
        assert success_count >= len(codes) * 0.6  # 至少 60% 成功率
        assert elapsed < 60  # 总时间应该小于 60 秒
