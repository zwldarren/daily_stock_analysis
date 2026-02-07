"""
单元测试 - AI 模型模块

测试范围:
- AnalysisResult 数据类
- 数据转换方法
- 辅助方法（emoji, stars等）
- Dashboard 数据处理
"""

import pytest

from stock_analyzer.domain.entities.analysis_result import AnalysisResult


# =============================================================================
# AnalysisResult 基础测试
# =============================================================================
class TestAnalysisResultBasic:
    """测试 AnalysisResult 基础功能"""

    def test_basic_creation(self) -> None:
        """测试创建基本的 AnalysisResult"""
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice="持有",
        )

        assert result.code == "600519"
        assert result.name == "贵州茅台"
        assert result.sentiment_score == 75
        assert result.trend_prediction == "看多"
        assert result.operation_advice == "持有"

    def test_default_values(self) -> None:
        """测试默认值设置"""
        result = AnalysisResult(
            code="000001",
            name="平安银行",
            sentiment_score=50,
            trend_prediction="震荡",
            operation_advice="观望",
        )

        # 验证默认值
        assert result.decision_type == "hold"
        assert result.confidence_level == "中"
        assert result.success is True
        assert result.error_message is None
        assert result.raw_response is None
        assert result.search_performed is False


# =============================================================================
# to_dict 方法测试
# =============================================================================
class TestAnalysisResultToDict:
    """测试 to_dict 方法"""

    def test_to_dict_basic(self) -> None:
        """测试基本字典转换"""
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice="持有",
            decision_type="hold",
            confidence_level="高",
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["code"] == "600519"
        assert data["name"] == "贵州茅台"
        assert data["sentiment_score"] == 75
        assert data["trend_prediction"] == "看多"
        assert data["operation_advice"] == "持有"
        assert data["decision_type"] == "hold"
        assert data["confidence_level"] == "高"

    def test_to_dict_with_dashboard(self) -> None:
        """测试包含 dashboard 的字典转换"""
        dashboard_data = {
            "core_conclusion": {
                "one_sentence": "贵州茅台业绩稳健，建议持有",
                "position_advice": {
                    "has_position": "继续持有",
                    "no_position": "逢低买入",
                },
            },
            "battle_plan": {
                "sniper_points": {"support": "1500", "resistance": "1800"},
                "action_checklist": ["关注Q3财报", "观察北向资金"],
            },
            "intelligence": {
                "risk_alerts": ["估值偏高", "行业竞争加剧"],
            },
        }

        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice="持有",
            dashboard=dashboard_data,
        )

        data = result.to_dict()

        assert data["dashboard"] == dashboard_data
        assert data["trend_analysis"] == ""
        assert data["technical_analysis"] == ""


# =============================================================================
# get_emoji 方法测试
# =============================================================================
class TestAnalysisResultGetEmoji:
    """测试 get_emoji 方法"""

    @pytest.mark.parametrize(
        "advice, expected",
        [
            ("买入", "🟢"),
            ("加仓", "🟢"),
            ("强烈买入", "💚"),
            ("持有", "🟡"),
            ("观望", "⚪"),
            ("减仓", "🟠"),
            ("卖出", "🔴"),
            ("强烈卖出", "❌"),
            ("未知建议", "🟡"),  # 默认
        ],
    )
    def test_get_emoji(self, advice: str, expected: str) -> None:
        """测试各种操作建议对应的 emoji"""
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice=advice,
        )

        assert result.get_emoji() == expected


# =============================================================================
# get_confidence_stars 方法测试
# =============================================================================
class TestAnalysisResultGetConfidenceStars:
    """测试 get_confidence_stars 方法"""

    @pytest.mark.parametrize(
        "level, expected",
        [
            ("高", "⭐⭐⭐"),
            ("中", "⭐⭐"),
            ("低", "⭐"),
            ("未知", "⭐⭐"),  # 默认
        ],
    )
    def test_get_confidence_stars(self, level: str, expected: str) -> None:
        """测试各种置信度对应的星级"""
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice="持有",
            confidence_level=level,
        )

        assert result.get_confidence_stars() == expected


# =============================================================================
# Dashboard 相关方法测试
# =============================================================================
class TestAnalysisResultDashboardMethods:
    """测试 Dashboard 相关方法"""

    @pytest.fixture
    def result_with_dashboard(self) -> AnalysisResult:
        """创建包含 dashboard 的 AnalysisResult"""
        return AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice="持有",
            dashboard={
                "core_conclusion": {
                    "one_sentence": "业绩稳健，建议持有",
                    "position_advice": {
                        "has_position": "继续持有",
                        "no_position": "逢低买入",
                    },
                },
                "battle_plan": {
                    "sniper_points": {
                        "support": "1500",
                        "resistance": "1800",
                    },
                    "action_checklist": ["关注财报", "观察资金流向"],
                },
                "intelligence": {
                    "risk_alerts": ["估值偏高"],
                },
            },
        )

    def test_get_core_conclusion(self, result_with_dashboard: AnalysisResult) -> None:
        """测试获取核心结论"""
        conclusion = result_with_dashboard.get_core_conclusion()
        assert conclusion == "业绩稳健，建议持有"

    def test_get_core_conclusion_fallback(self) -> None:
        """测试获取核心结论回退到 analysis_summary"""
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice="持有",
            analysis_summary="这是分析摘要",
        )
        # 没有 dashboard 时应该返回 analysis_summary
        # 注意：get_core_conclusion 在 dashboard 为 None 时返回 analysis_summary
        conclusion = result.get_core_conclusion()
        assert conclusion == "这是分析摘要"

    def test_get_position_advice(self, result_with_dashboard: AnalysisResult) -> None:
        """测试获取持仓建议"""
        advice_with = result_with_dashboard.get_position_advice(has_position=True)
        assert advice_with == "继续持有"

        advice_without = result_with_dashboard.get_position_advice(has_position=False)
        assert advice_without == "逢低买入"

    def test_get_sniper_points(self, result_with_dashboard: AnalysisResult) -> None:
        """测试获取狙击点位"""
        points = result_with_dashboard.get_sniper_points()
        assert points == {"support": "1500", "resistance": "1800"}

    def test_get_checklist(self, result_with_dashboard: AnalysisResult) -> None:
        """测试获取检查清单"""
        checklist = result_with_dashboard.get_checklist()
        assert checklist == ["关注财报", "观察资金流向"]

    def test_get_risk_alerts(self, result_with_dashboard: AnalysisResult) -> None:
        """测试获取风险警报"""
        alerts = result_with_dashboard.get_risk_alerts()
        assert alerts == ["估值偏高"]

    def test_dashboard_methods_with_none(self) -> None:
        """测试 dashboard 为 None 时的行为"""
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=75,
            trend_prediction="看多",
            operation_advice="持有",
            dashboard=None,
        )

        # 所有方法应该返回空值或默认值
        assert result.get_sniper_points() == {}
        assert result.get_checklist() == []
        assert result.get_risk_alerts() == []
