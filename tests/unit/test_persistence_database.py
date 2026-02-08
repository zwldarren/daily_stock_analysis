"""Tests for storage/persistence layer."""

from stock_analyzer.infrastructure.persistence.database import DatabaseManager


class TestParseSniperValue:
    """测试解析狙击点位数值"""

    def test_direct_numeric_values(self):
        """1. 正常数值"""
        assert DatabaseManager._parse_sniper_value(100) == 100.0
        assert DatabaseManager._parse_sniper_value(100.5) == 100.5
        assert DatabaseManager._parse_sniper_value("100") == 100.0
        assert DatabaseManager._parse_sniper_value("100.5") == 100.5

    def test_chinese_description_with_yuan(self):
        """2. 包含中文描述和元"""
        assert DatabaseManager._parse_sniper_value("建议在 100 元附近买入") == 100.0
        assert DatabaseManager._parse_sniper_value("价格：100.5元") == 100.5

    def test_bug_fix_ma_interference(self):
        """3. 包含干扰数字（修复的Bug场景）

        之前 "MA5" 会被错误提取为 5.0，现在应该提取 "元" 前面的 100
        """
        text_bug = "无法给出。需等待MA5数据恢复，在股价回踩MA5且乖离率<2%时考虑100元"
        assert DatabaseManager._parse_sniper_value(text_bug) == 100.0

    def test_more_interference_scenarios(self):
        """4. 更多干扰场景"""
        text_complex = "MA10为20.5，建议在30元买入"
        assert DatabaseManager._parse_sniper_value(text_complex) == 30.0

        # 测试没有冒号的情况
        assert DatabaseManager._parse_sniper_value("30元") == 30.0

        # 测试多个数字在"元"之前
        assert DatabaseManager._parse_sniper_value("MA5 10 20元") == 20.0

    def test_invalid_inputs(self):
        """5. 无效输入"""
        assert DatabaseManager._parse_sniper_value(None) is None
        assert DatabaseManager._parse_sniper_value("") is None
        assert DatabaseManager._parse_sniper_value("没有数字") is None
        assert DatabaseManager._parse_sniper_value("MA5但没有元") is None
