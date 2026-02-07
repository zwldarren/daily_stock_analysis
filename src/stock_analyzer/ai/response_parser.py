"""
响应解析模块

负责解析AI返回的响应文本
"""

import json
import logging
import re

from json_repair import repair_json

from stock_analyzer.domain.entities.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


class ResponseParser:
    """响应解析器"""

    @staticmethod
    def parse(response_text: str, code: str, name: str) -> AnalysisResult:
        """
        解析AI响应

        尝试从响应中提取 JSON 格式的分析结果
        如果解析失败，尝试智能提取或返回默认结果
        """
        try:
            cleaned_text = ResponseParser._clean_response(response_text)
            json_start = cleaned_text.find("{")
            json_end = cleaned_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = cleaned_text[json_start:json_end]
                json_str = ResponseParser._fix_json(json_str)
                data = json.loads(json_str)
                return ResponseParser._build_result(data, code, name, response_text)
            else:
                logger.warning("无法从响应中提取 JSON，使用原始文本分析")
                return ResponseParser._parse_text(response_text, code, name)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}，尝试从文本提取")
            return ResponseParser._parse_text(response_text, code, name)

    @staticmethod
    def _clean_response(response_text: str) -> str:
        """清理响应文本"""
        cleaned = response_text
        if "```json" in cleaned:
            cleaned = cleaned.replace("```json", "").replace("```", "")
        elif "```" in cleaned:
            cleaned = cleaned.replace("```", "")
        return cleaned

    @staticmethod
    def _fix_json(json_str: str) -> str:
        """修复常见的 JSON 格式问题"""
        # 移除注释
        json_str = re.sub(r"//.*?\n", "\n", json_str)
        json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)

        # 修复尾随逗号
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)

        # 确保布尔值是小写
        json_str = json_str.replace("True", "true").replace("False", "false")

        # fix by json-repair
        json_str = repair_json(json_str)

        return json_str

    @staticmethod
    def _build_result(data: dict, code: str, name: str, raw_response: str) -> AnalysisResult:
        """从解析的数据构建结果对象"""
        dashboard = data.get("dashboard")

        # 优先使用 AI 返回的股票名称
        ai_stock_name = data.get("stock_name")
        if ai_stock_name and (name.startswith("股票") or name == code or "Unknown" in name):
            name = ai_stock_name

        # 解析 decision_type
        decision_type = data.get("decision_type", "")
        if not decision_type:
            op = data.get("operation_advice", "持有")
            if op in ["买入", "加仓", "强烈买入"]:
                decision_type = "buy"
            elif op in ["卖出", "减仓", "强烈卖出"]:
                decision_type = "sell"
            else:
                decision_type = "hold"

        return AnalysisResult(
            code=code,
            name=name,
            sentiment_score=int(data.get("sentiment_score", 50)),
            trend_prediction=data.get("trend_prediction", "震荡"),
            operation_advice=data.get("operation_advice", "持有"),
            decision_type=decision_type,
            confidence_level=data.get("confidence_level", "中"),
            dashboard=dashboard,
            trend_analysis=data.get("trend_analysis", ""),
            short_term_outlook=data.get("short_term_outlook", ""),
            medium_term_outlook=data.get("medium_term_outlook", ""),
            technical_analysis=data.get("technical_analysis", ""),
            ma_analysis=data.get("ma_analysis", ""),
            volume_analysis=data.get("volume_analysis", ""),
            pattern_analysis=data.get("pattern_analysis", ""),
            fundamental_analysis=data.get("fundamental_analysis", ""),
            sector_position=data.get("sector_position", ""),
            company_highlights=data.get("company_highlights", ""),
            news_summary=data.get("news_summary", ""),
            market_sentiment=data.get("market_sentiment", ""),
            hot_topics=data.get("hot_topics", ""),
            analysis_summary=data.get("analysis_summary", "分析完成"),
            key_points=data.get("key_points", ""),
            risk_warning=data.get("risk_warning", ""),
            buy_reason=data.get("buy_reason", ""),
            search_performed=data.get("search_performed", False),
            data_sources=data.get("data_sources", "技术面数据"),
            raw_response=raw_response,
            success=True,
        )

    @staticmethod
    def _parse_text(response_text: str, code: str, name: str) -> AnalysisResult:
        """从纯文本响应中尽可能提取分析信息"""
        sentiment_score = 50
        trend = "震荡"
        advice = "持有"
        decision_type = "hold"

        text_lower = response_text.lower()

        positive_keywords = [
            "看多",
            "买入",
            "上涨",
            "突破",
            "强势",
            "利好",
            "加仓",
            "bullish",
            "buy",
        ]
        negative_keywords = [
            "看空",
            "卖出",
            "下跌",
            "跌破",
            "弱势",
            "利空",
            "减仓",
            "bearish",
            "sell",
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)

        if positive_count > negative_count + 1:
            sentiment_score = 65
            trend = "看多"
            advice = "买入"
            decision_type = "buy"
        elif negative_count > positive_count + 1:
            sentiment_score = 35
            trend = "看空"
            advice = "卖出"
            decision_type = "sell"

        summary = response_text[:500] if response_text else "无分析结果"

        return AnalysisResult(
            code=code,
            name=name,
            sentiment_score=sentiment_score,
            trend_prediction=trend,
            operation_advice=advice,
            decision_type=decision_type,
            confidence_level="低",
            analysis_summary=summary,
            key_points="JSON解析失败，仅供参考",
            risk_warning="分析结果可能不准确，建议结合其他信息判断",
            raw_response=response_text,
            success=True,
        )
