"""
===================================
A股自选股智能分析系统 - AI分析层
===================================

职责：
1. 使用 litellm 调用多种 LLM API 进行股票分析
2. 支持 100+ providers（deepseek, gemini, openai, anthropic 等）
3. 支持主备模型自动回退
4. 结合技术面和消息面生成分析报告
"""

import logging
import time
from typing import Any

from stock_analyzer.ai.clients import LiteLLMClient
from stock_analyzer.ai.prompt_builder import PromptBuilder
from stock_analyzer.ai.response_parser import ResponseParser
from stock_analyzer.ai.snapshot_builder import MarketSnapshotBuilder
from stock_analyzer.config import get_config
from stock_analyzer.domain import get_stock_name_from_context
from stock_analyzer.domain.entities.analysis_result import AnalysisResult
from stock_analyzer.domain.services.interfaces import IAIAnalyzer
from stock_analyzer.utils.fallback import create_sequential_fallback

logger = logging.getLogger(__name__)


class AIAnalyzer(IAIAnalyzer):
    """
    AI 分析器 - 基于 litellm 的多 provider 支持

    职责：
    1. 调用配置的 LLM API 进行股票分析
    2. 支持主备模型自动回退
    3. 结合预先搜索的新闻和技术面数据生成分析报告
    4. 解析 AI 返回的 JSON 格式结果

    使用方式：
        analyzer = AIAnalyzer()
        result = analyzer.analyze(context, news_context)
    """

    def __init__(self):
        """
        初始化 AI 分析器

        自动从配置读取主模型和备选模型配置
        """
        config = get_config()

        # 初始化主模型客户端
        self._primary_client = LiteLLMClient(
            model=config.ai.llm_model,
            api_key=config.ai.llm_api_key,
            base_url=config.ai.llm_base_url,
        )

        # 初始化备选模型客户端（如果配置了）
        self._fallback_client: LiteLLMClient | None = None
        if config.ai.llm_fallback_model and config.ai.llm_fallback_api_key:
            self._fallback_client = LiteLLMClient(
                model=config.ai.llm_fallback_model,
                api_key=config.ai.llm_fallback_api_key,
                base_url=config.ai.llm_fallback_base_url,
            )

        # 预创建回退策略对象
        self._fallback_handler = create_sequential_fallback(name="ai_llm_fallback")

        # 检查可用性
        if not self.is_available():
            logger.warning("未配置有效的 LLM API Key，AI 分析功能将不可用")
        else:
            logger.info(f"AI 分析器初始化成功 (主模型: {config.ai.llm_model})")
            if self._fallback_client and self._fallback_client.is_available():
                logger.info(f"备选模型已配置: {config.ai.llm_fallback_model}")

    def is_available(self) -> bool:
        """检查分析器是否可用"""
        return self._primary_client.is_available() or (
            self._fallback_client is not None and self._fallback_client.is_available()
        )

    def _call_api(self, prompt: str, generation_config: dict) -> str:
        """
        调用 AI API，支持主备模型回退

        Args:
            prompt: 提示词
            generation_config: 生成配置

        Returns:
            响应文本
        """
        if not self.is_available():
            raise Exception("没有可用的 AI 客户端")

        def call_primary() -> str:
            return self._primary_client.generate(prompt, generation_config)

        # 如果有备选模型且主模型可用，使用回退策略
        if self._fallback_client and self._fallback_client.is_available():

            def call_fallback() -> str:
                if self._fallback_client is None:
                    raise Exception("备选模型客户端未初始化")
                return self._fallback_client.generate(prompt, generation_config)

            if self._primary_client.is_available():
                return self._fallback_handler.execute(call_primary, call_fallback)
            else:
                return call_fallback()

        # 只有主模型
        if self._primary_client.is_available():
            return call_primary()

        raise Exception("没有可用的 AI 客户端")

    def analyze(self, context: dict[str, Any], news_context: str | None = None) -> AnalysisResult:
        """
        分析单只股票

        流程：
        1. 格式化输入数据（技术面 + 新闻）
        2. 调用 LLM API（带重试和模型回退）
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
        request_delay = config.ai.llm_request_delay
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
                risk_warning="请配置 LLM_API_KEY 后重试",
                success=False,
                error_message="LLM API Key 未配置",
            )

        try:
            # 格式化输入
            prompt = PromptBuilder.build_analysis_prompt(context, name, news_context)

            # 获取模型名称
            model_name = config.ai.llm_model

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
                "temperature": config.ai.llm_temperature,
                "max_output_tokens": config.ai.llm_max_tokens,
            }

            logger.info(f"[LLM调用] 开始调用 {model_name} API...")

            # 使用带重试的 API 调用
            start_time = time.time()
            response_text = self._call_api(prompt, generation_config)
            elapsed = time.time() - start_time

            logger.info(f"[LLM返回] {model_name} API 响应成功, 耗时 {elapsed:.2f}s, 响应长度 {len(response_text)} 字符")

            # 记录响应预览
            response_preview = response_text[:300] + "..." if len(response_text) > 300 else response_text
            logger.info(f"[LLM返回 预览]\n{response_preview}")
            logger.debug(
                f"=== {model_name} 完整响应 ({len(response_text)}字符) ===\n{response_text}\n=== End Response ==="
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

    def batch_analyze(
        self,
        contexts: list[dict[str, Any]],
        delay_between: float = 2.0,
        news_contexts: list[str | None] | None = None,
    ) -> list[AnalysisResult]:
        """
        批量分析多只股票

        Args:
            contexts: 上下文数据列表
            delay_between: 每次分析之间的延迟（秒）
            news_contexts: 新闻上下文列表（与contexts一一对应）

        Returns:
            AnalysisResult 列表
        """
        results = []

        for i, context in enumerate(contexts):
            if i > 0:
                logger.debug(f"等待 {delay_between} 秒后继续...")
                time.sleep(delay_between)

            news_context = news_contexts[i] if news_contexts and i < len(news_contexts) else None
            result = self.analyze(context, news_context=news_context)
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
def get_analyzer() -> AIAnalyzer:
    """获取 AI 分析器实例"""
    return AIAnalyzer()


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

    analyzer = AIAnalyzer()

    if analyzer.is_available():
        print("=== AI 分析测试 ===")
        result = analyzer.analyze(test_context)
        print(f"分析结果: {result.to_dict()}")
    else:
        print("LLM API 未配置，跳过测试")
