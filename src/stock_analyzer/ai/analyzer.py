"""
===================================
A股自选股智能分析系统 - AI分析层
===================================

职责：
1. 封装 Gemini API 调用逻辑
2. 利用 Google Search Grounding 获取实时新闻
3. 结合技术面和消息面生成分析报告
"""

import logging
import time
from typing import Any

from stock_analyzer.ai.clients import GeminiClient, OpenAIClient
from stock_analyzer.ai.prompt_builder import PromptBuilder
from stock_analyzer.ai.response_parser import ResponseParser
from stock_analyzer.ai.snapshot_builder import MarketSnapshotBuilder
from stock_analyzer.config import get_config
from stock_analyzer.domain import get_stock_name_from_context
from stock_analyzer.domain.entities.analysis_result import AnalysisResult
from stock_analyzer.domain.services.interfaces import IAIAnalyzer
from stock_analyzer.utils.fallback import create_sequential_fallback

logger = logging.getLogger(__name__)


class GeminiAnalyzer(IAIAnalyzer):
    """
    Gemini AI 分析器

    职责：
    1. 调用 Google Gemini API 进行股票分析
    2. 结合预先搜索的新闻和技术面数据生成分析报告
    3. 解析 AI 返回的 JSON 格式结果

    使用方式：
        analyzer = GeminiAnalyzer()
        result = analyzer.analyze(context, news_context)
    """

    def __init__(self, api_key: str | None = None):
        """
        初始化 AI 分析器

        优先级：Gemini > OpenAI 兼容 API

        Args:
            api_key: Gemini API Key（可选，默认从配置读取）
        """
        self._gemini_client = GeminiClient(api_key)
        self._openai_client = OpenAIClient()
        self._use_openai = False

        # 如果Gemini不可用，检查OpenAI
        if not self._gemini_client.is_available():
            if self._openai_client.is_available():
                self._use_openai = True
                logger.info("使用 OpenAI 兼容 API 作为 AI 后端")
            else:
                logger.warning("未配置任何 AI API Key，AI 分析功能将不可用")

    def is_available(self) -> bool:
        """检查分析器是否可用"""
        return self._gemini_client.is_available() or self._openai_client.is_available()

    def _call_api(self, prompt: str, generation_config: dict) -> str:
        """
        调用 AI API，使用统一的回退策略

        Args:
            prompt: 提示词
            generation_config: 生成配置

        Returns:
            响应文本
        """
        if not self.is_available():
            raise Exception("没有可用的 AI 客户端")

        # 定义主操作和回退操作
        def call_gemini() -> str:
            return self._gemini_client.generate(prompt, generation_config)

        def call_openai() -> str:
            return self._openai_client.generate(prompt, generation_config)

        # 根据配置决定主操作
        if self._use_openai:
            # OpenAI 为主，Gemini 为回退
            if self._gemini_client.is_available():
                fallback = create_sequential_fallback(name="ai_openai_fallback")
                return fallback.execute(call_openai, call_gemini)
            return call_openai()
        else:
            # Gemini 为主，OpenAI 为回退
            if self._openai_client.is_available():
                fallback = create_sequential_fallback(name="ai_gemini_fallback")
                return fallback.execute(call_gemini, call_openai)
            return call_gemini()

    def analyze(self, context: dict[str, Any], news_context: str | None = None) -> AnalysisResult:
        """
        分析单只股票

        流程：
        1. 格式化输入数据（技术面 + 新闻）
        2. 调用 Gemini API（带重试和模型切换）
        3. 解析 JSON 响应
        4. 返回结构化结果

        Args:
            context: 从 storage.get_analysis_context() 获取的上下文数据
            news_context: 预先搜索的新闻内容（可选）

        Returns:
            AnalysisResult 对象
        """
        code = context.get("code", "Unknown")
        config = get_config()

        # 请求前增加延时
        request_delay = config.ai.gemini_request_delay
        if request_delay > 0:
            logger.debug(f"[LLM] 请求前等待 {request_delay:.1f} 秒...")
            time.sleep(request_delay)

        # 获取股票名称
        name = context.get("stock_name")
        if not name or name.startswith("股票"):
            if "realtime" in context and context["realtime"].get("name"):
                name = context["realtime"]["name"]
            else:
                name = get_stock_name_from_context(code, context)

        # 如果模型不可用，返回默认结果
        if not self.is_available():
            return AnalysisResult(
                code=code,
                name=name,
                sentiment_score=50,
                trend_prediction="震荡",
                operation_advice="持有",
                confidence_level="低",
                analysis_summary="AI 分析功能未启用（未配置 API Key）",
                risk_warning="请配置 Gemini API Key 后重试",
                success=False,
                error_message="Gemini API Key 未配置",
            )

        try:
            # 格式化输入
            prompt = PromptBuilder.build_analysis_prompt(context, name, news_context)

            # 获取模型名称
            model_name = "unknown"
            if self._use_openai:
                model_name = "openai-compatible"
            elif self._gemini_client._current_model_name:
                model_name = self._gemini_client._current_model_name

            logger.info(f"========== AI 分析 {name}({code}) ==========")
            logger.info(f"[LLM配置] 模型: {model_name}")
            logger.info(f"[LLM配置] Prompt 长度: {len(prompt)} 字符")
            logger.info(f"[LLM配置] 是否包含新闻: {'是' if news_context else '否'}")

            # 记录完整 prompt
            prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
            logger.info(f"[LLM Prompt 预览]\n{prompt_preview}")
            logger.debug(f"=== 完整 Prompt ({len(prompt)}字符) ===\n{prompt}\n=== End Prompt ===")

            # 设置生成配置
            generation_config = {
                "temperature": config.ai.gemini_temperature,
                "max_output_tokens": 8192,
            }

            api_provider = "OpenAI" if self._use_openai else "Gemini"
            logger.info(f"[LLM调用] 开始调用 {api_provider} API...")

            # 使用带重试的 API 调用
            start_time = time.time()
            response_text = self._call_api(prompt, generation_config)
            elapsed = time.time() - start_time

            logger.info(
                f"[LLM返回] {api_provider} API 响应成功, 耗时 {elapsed:.2f}s, 响应长度 {len(response_text)} 字符"
            )

            # 记录响应预览
            response_preview = response_text[:300] + "..." if len(response_text) > 300 else response_text
            logger.info(f"[LLM返回 预览]\n{response_preview}")
            logger.debug(
                f"=== {api_provider} 完整响应 ({len(response_text)}字符) ===\n{response_text}\n=== End Response ==="
            )

            # 解析响应
            result = ResponseParser.parse(response_text, code, name)
            result.raw_response = response_text
            result.search_performed = bool(news_context)
            result.market_snapshot = MarketSnapshotBuilder.build(context)

            logger.info(f"[LLM解析] {name}({code}) 分析完成: {result.trend_prediction}, 评分 {result.sentiment_score}")

            return result

        except Exception as e:
            logger.error(f"AI 分析 {name}({code}) 失败: {e}")
            return AnalysisResult(
                code=code,
                name=name,
                sentiment_score=50,
                trend_prediction="震荡",
                operation_advice="持有",
                confidence_level="低",
                analysis_summary=f"分析过程出错: {str(e)[:100]}",
                risk_warning="分析失败，请稍后重试或手动分析",
                success=False,
                error_message=str(e),
            )

    def batch_analyze(self, contexts: list[dict[str, Any]], delay_between: float = 2.0) -> list[AnalysisResult]:
        """
        批量分析多只股票

        Args:
            contexts: 上下文数据列表
            delay_between: 每次分析之间的延迟（秒）

        Returns:
            AnalysisResult 列表
        """
        results = []

        for i, context in enumerate(contexts):
            if i > 0:
                logger.debug(f"等待 {delay_between} 秒后继续...")
                time.sleep(delay_between)

            result = self.analyze(context)
            results.append(result)

        return results

    def generate_market_review(self, prompt: str, generation_config: dict[str, Any]) -> str | None:
        """
        生成市场复盘报告

        Args:
            prompt: 提示词
            generation_config: 生成配置

        Returns:
            生成的复盘报告文本，失败返回 None
        """
        try:
            return self._call_api(prompt, generation_config)
        except Exception as e:
            logger.error(f"生成市场复盘报告失败: {e}")
            return None


# 便捷函数
def get_analyzer() -> GeminiAnalyzer:
    """获取 Gemini 分析器实例"""
    return GeminiAnalyzer()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)

    test_context = {
        "code": "600519",
        "date": "2026-01-09",
        "today": {
            "open": 1800.0,
            "high": 1850.0,
            "low": 1780.0,
            "close": 1820.0,
            "volume": 10000000,
            "amount": 18200000000,
            "pct_chg": 1.5,
            "ma5": 1810.0,
            "ma10": 1800.0,
            "ma20": 1790.0,
            "volume_ratio": 1.2,
        },
        "ma_status": "多头排列 📈",
        "volume_change_ratio": 1.3,
        "price_change_ratio": 1.5,
    }

    analyzer = GeminiAnalyzer()

    if analyzer.is_available():
        print("=== AI 分析测试 ===")
        result = analyzer.analyze(test_context)
        print(f"分析结果: {result.to_dict()}")
    else:
        print("Gemini API 未配置，跳过测试")
