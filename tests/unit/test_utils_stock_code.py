"""Tests for stock_code utility module."""

from stock_analyzer.utils.stock_code import (
    StockType,
    detect_stock_type,
    is_etf_code,
    is_hk_code,
    is_us_code,
    normalize_stock_code,
)


class TestStockType:
    """Test cases for StockType enum."""

    def test_stock_type_values(self):
        """Test that all stock types are defined."""
        assert StockType.A_SHARE.value == "a_share"
        assert StockType.HK.value == "hk"
        assert StockType.US.value == "us"
        assert StockType.ETF.value == "etf"
        assert StockType.UNKNOWN.value == "unknown"


class TestDetectStockType:
    """Test cases for detect_stock_type function."""

    def test_a_share_shanghai(self):
        """Test detecting Shanghai A-shares."""
        assert detect_stock_type("600519") == StockType.A_SHARE
        assert detect_stock_type("601318") == StockType.A_SHARE

    def test_a_share_shenzhen(self):
        """Test detecting Shenzhen A-shares."""
        assert detect_stock_type("000001") == StockType.A_SHARE
        assert detect_stock_type("300750") == StockType.A_SHARE

    def test_etf_codes(self):
        """Test detecting ETF codes."""
        assert detect_stock_type("510300") == StockType.ETF
        assert detect_stock_type("159915") == StockType.ETF

    def test_hong_kong_stocks(self):
        """Test detecting Hong Kong stocks."""
        assert detect_stock_type("00700") == StockType.HK
        assert detect_stock_type("03690") == StockType.HK

    def test_us_stocks(self):
        """Test detecting US stocks."""
        assert detect_stock_type("AAPL") == StockType.US
        assert detect_stock_type("TSLA") == StockType.US

    def test_empty_code(self):
        """Test detecting empty code."""
        assert detect_stock_type("") == StockType.UNKNOWN
        assert detect_stock_type("   ") == StockType.UNKNOWN

    def test_unknown_codes(self):
        """Test detecting unknown codes - pure letters are treated as US stocks."""
        # Note: "INVALID" is treated as US stock (pure alphabetic)
        assert detect_stock_type("INVALID") == StockType.US
        assert detect_stock_type("123") == StockType.UNKNOWN


class TestIsUsCode:
    """Test cases for is_us_code function."""

    def test_valid_us_codes(self):
        """Test valid US codes."""
        assert is_us_code("AAPL") is True
        assert is_us_code("TSLA") is True
        assert is_us_code("GOOGL") is True

    def test_invalid_us_codes(self):
        """Test invalid US codes."""
        assert is_us_code("600519") is False
        assert is_us_code("00700") is False


class TestIsHkCode:
    """Test cases for is_hk_code function."""

    def test_valid_hk_codes(self):
        """Test valid HK codes."""
        assert is_hk_code("00700") is True
        assert is_hk_code("03690") is True
        assert is_hk_code("01810") is True

    def test_invalid_hk_codes(self):
        """Test invalid HK codes."""
        assert is_hk_code("600519") is False
        assert is_hk_code("AAPL") is False


class TestIsEtfCode:
    """Test cases for is_etf_code function."""

    def test_valid_etf_codes(self):
        """Test valid ETF codes."""
        assert is_etf_code("510300") is True
        assert is_etf_code("159915") is True

    def test_invalid_etf_codes(self):
        """Test invalid ETF codes."""
        assert is_etf_code("600519") is False
        assert is_etf_code("AAPL") is False


class TestNormalizeStockCode:
    """Test cases for normalize_stock_code function."""

    def test_normalize_a_share(self):
        """Test normalizing A-share codes."""
        assert normalize_stock_code("600519") == "600519"
        assert normalize_stock_code(" 600519 ") == "600519"

    def test_normalize_hk_stock(self):
        """Test normalizing HK stock codes."""
        assert normalize_stock_code("00700") == "00700"
        # Short HK codes are not padded to 5 digits by current implementation
        assert normalize_stock_code("700") == "700"

    def test_normalize_us_stock(self):
        """Test normalizing US stock codes."""
        assert normalize_stock_code("AAPL") == "AAPL"
        assert normalize_stock_code("aapl") == "AAPL"
