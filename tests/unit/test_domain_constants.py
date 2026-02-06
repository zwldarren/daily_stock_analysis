"""Tests for domain constants."""

from stock_analyzer.domain.constants import STOCK_NAME_MAP


class TestStockNameMap:
    """Test cases for STOCK_NAME_MAP constant."""

    def test_stock_name_map_exists(self):
        """Test that STOCK_NAME_MAP exists and is a dict."""
        assert isinstance(STOCK_NAME_MAP, dict)

    def test_a_share_stocks(self):
        """Test A-share stocks are in the map."""
        assert STOCK_NAME_MAP.get("600519") == "贵州茅台"
        assert STOCK_NAME_MAP.get("000001") == "平安银行"
        assert STOCK_NAME_MAP.get("300750") == "宁德时代"

    def test_us_stocks(self):
        """Test US stocks are in the map."""
        assert STOCK_NAME_MAP.get("AAPL") == "苹果"
        assert STOCK_NAME_MAP.get("TSLA") == "特斯拉"
        assert STOCK_NAME_MAP.get("NVDA") == "英伟达"

    def test_hk_stocks(self):
        """Test HK stocks are in the map."""
        assert STOCK_NAME_MAP.get("00700") == "腾讯控股"
        assert STOCK_NAME_MAP.get("03690") == "美团"
        assert STOCK_NAME_MAP.get("01810") == "小米集团"

    def test_nonexistent_stock(self):
        """Test that non-existent stocks return None."""
        assert STOCK_NAME_MAP.get("999999") is None
        assert STOCK_NAME_MAP.get("INVALID") is None
