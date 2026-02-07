"""
搜索服务

提供统一的搜索服务接口，管理多个搜索引擎和搜索策略
"""

import logging
import time
from datetime import datetime
from typing import Any

from stock_analyzer.domain.models import SearchResponse
from stock_analyzer.domain.services.interfaces import ISearchService
from stock_analyzer.infrastructure.external.search.providers import (
    BaseSearchProvider,
    BochaSearchProvider,
    BraveSearchProvider,
    SerpAPISearchProvider,
    TavilySearchProvider,
)

logger = logging.getLogger(__name__)


class SearchService(ISearchService):
    """
    搜索服务

    功能：
    1. 管理多个搜索引擎
    2. 自动故障转移
    3. 结果聚合和格式化
    """

    # 增强搜索关键词模板
    ENHANCED_SEARCH_KEYWORDS = [
        "{name} 股票 今日 股价",
        "{name} {code} 最新 行情 走势",
        "{name} 股票 分析 走势图",
        "{name} K线 技术分析",
        "{name} {code} 涨跌 成交量",
    ]

    def __init__(
        self,
        bocha_keys: list[str] | None = None,
        tavily_keys: list[str] | None = None,
        brave_keys: list[str] | None = None,
        serpapi_keys: list[str] | None = None,
    ):
        """
        初始化搜索服务

        Args:
            bocha_keys: 博查搜索 API Key 列表
            tavily_keys: Tavily API Key 列表
            brave_keys: Brave Search API Key 列表
            serpapi_keys: SerpAPI Key 列表
        """
        self._providers: list[BaseSearchProvider] = []

        # 初始化搜索引擎（按优先级排序）
        # 1. Bocha 优先（中文搜索优化，AI摘要）
        if bocha_keys:
            self._providers.append(BochaSearchProvider(bocha_keys))
            logger.info(f"已配置 Bocha 搜索，共 {len(bocha_keys)} 个 API Key")

        # 2. Tavily（免费额度更多，每月 1000 次）
        if tavily_keys:
            self._providers.append(TavilySearchProvider(tavily_keys))
            logger.info(f"已配置 Tavily 搜索，共 {len(tavily_keys)} 个 API Key")

        # 3. Brave Search（隐私优先，全球覆盖）
        if brave_keys:
            self._providers.append(BraveSearchProvider(brave_keys))
            logger.info(f"已配置 Brave 搜索，共 {len(brave_keys)} 个 API Key")

        # 4. SerpAPI 作为备选（每月 100 次）
        if serpapi_keys:
            self._providers.append(SerpAPISearchProvider(serpapi_keys))
            logger.info(f"已配置 SerpAPI 搜索，共 {len(serpapi_keys)} 个 API Key")

        if not self._providers:
            logger.warning("未配置任何搜索引擎 API Key，新闻搜索功能将不可用")

    @property
    def is_available(self) -> bool:
        """检查是否有可用的搜索引擎"""
        return any(p.is_available for p in self._providers)

    def search_stock_news(
        self,
        stock_code: str,
        stock_name: str,
        max_results: int = 5,
        focus_keywords: list[str] | None = None,
    ) -> SearchResponse:
        """
        搜索股票相关新闻

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            max_results: 最大返回结果数
            focus_keywords: 重点关注的关键词列表

        Returns:
            SearchResponse 对象
        """
        # 智能确定搜索时间范围
        today_weekday = datetime.now().weekday()
        if today_weekday == 0:  # 周一
            search_days = 3
        elif today_weekday >= 5:  # 周六(5)、周日(6)
            search_days = 2
        else:  # 周二(1) - 周五(4)
            search_days = 1

        # 构建搜索查询
        query = " ".join(focus_keywords) if focus_keywords else f"{stock_name} {stock_code} 股票 最新消息"

        logger.info(f"搜索股票新闻: {stock_name}({stock_code}), query='{query}', 时间范围: 近{search_days}天")

        # 依次尝试各个搜索引擎
        for provider in self._providers:
            if not provider.is_available:
                continue

            response = provider.search(query, max_results, days=search_days)

            if response.success and response.results:
                logger.info(f"使用 {provider.name} 搜索成功")
                return response
            else:
                logger.warning(f"{provider.name} 搜索失败: {response.error_message}，尝试下一个引擎")

        # 所有引擎都失败
        return SearchResponse(
            query=query,
            results=[],
            provider="None",
            success=False,
            error_message="所有搜索引擎都不可用或搜索失败",
        )

    def search_comprehensive_intel(
        self, stock_code: str, stock_name: str, max_searches: int = 3
    ) -> dict[str, SearchResponse]:
        """
        多维度情报搜索

        搜索维度：
        1. 最新消息 - 近期新闻动态
        2. 风险排查 - 减持、处罚、利空
        3. 业绩预期 - 年报预告、业绩快报
        """
        results = {}
        search_count = 0

        # 定义搜索维度
        search_dimensions = [
            {
                "name": "latest_news",
                "query": f"{stock_name} {stock_code} 最新 新闻 重大 事件",
                "desc": "最新消息",
            },
            {
                "name": "market_analysis",
                "query": f"{stock_name} 研报 目标价 评级 深度分析",
                "desc": "机构分析",
            },
            {
                "name": "risk_check",
                "query": f"{stock_name} 减持 处罚 违规 诉讼 利空 风险",
                "desc": "风险排查",
            },
            {
                "name": "earnings",
                "query": f"{stock_name} 业绩预告 财报 营收 净利润 同比增长",
                "desc": "业绩预期",
            },
            {
                "name": "industry",
                "query": f"{stock_name} 所在行业 竞争对手 市场份额 行业前景",
                "desc": "行业分析",
            },
        ]

        logger.info(f"开始多维度情报搜索: {stock_name}({stock_code})")

        # 轮流使用不同的搜索引擎
        # 选择搜索引擎（轮流使用）
        available_providers = [p for p in self._providers if p.is_available]
        if not available_providers:
            return results

        for search_count, dim in enumerate(search_dimensions):
            if search_count >= max_searches:
                break

            provider = available_providers[search_count % len(available_providers)]

            logger.info(f"[情报搜索] {dim['desc']}: 使用 {provider.name}")

            response = provider.search(dim["query"], max_results=3)
            results[dim["name"]] = response

            if response.success:
                logger.info(f"[情报搜索] {dim['desc']}: 获取 {len(response.results)} 条结果")
            else:
                logger.warning(f"[情报搜索] {dim['desc']}: 搜索失败 - {response.error_message}")

            # 短暂延迟避免请求过快
            time.sleep(0.5)

        return results

    def format_intel_report(self, intel_results: dict[str, SearchResponse], stock_name: str) -> str:
        """
        格式化情报搜索结果为报告
        """
        lines = [f"【{stock_name} 情报搜索结果】"]

        # 维度展示顺序
        display_order = ["latest_news", "market_analysis", "risk_check", "earnings", "industry"]

        for dim_name in display_order:
            if dim_name not in intel_results:
                continue

            resp = intel_results[dim_name]

            # 获取维度描述
            dim_desc = dim_name
            if dim_name == "latest_news":
                dim_desc = "📰 最新消息"
            elif dim_name == "market_analysis":
                dim_desc = "📈 机构分析"
            elif dim_name == "risk_check":
                dim_desc = "⚠️ 风险排查"
            elif dim_name == "earnings":
                dim_desc = "📊 业绩预期"
            elif dim_name == "industry":
                dim_desc = "🏭 行业分析"

            lines.append(f"\n{dim_desc} (来源: {resp.provider}):")
            if resp.success and resp.results:
                for i, r in enumerate(resp.results[:4], 1):
                    date_str = f" [{r.published_date}]" if r.published_date else ""
                    lines.append(f"  {i}. {r.title}{date_str}")
                    snippet = r.snippet[:150] if len(r.snippet) > 20 else r.snippet
                    lines.append(f"     {snippet}...")
            else:
                lines.append("  未找到相关信息")

        return "\n".join(lines)

    def search_stock_price_fallback(
        self, stock_code: str, stock_name: str, max_attempts: int = 3, max_results: int = 5
    ) -> SearchResponse:
        """
        Enhance search when data sources fail.
        """
        if not self.is_available:
            return SearchResponse(
                query=f"{stock_name} 股价走势",
                results=[],
                provider="None",
                success=False,
                error_message="未配置搜索引擎 API Key",
            )

        logger.info(f"[增强搜索] 数据源失败，启动增强搜索: {stock_name}({stock_code})")

        all_results = []
        seen_urls = set()
        successful_providers = []

        # 使用多个关键词模板搜索
        for i, keyword_template in enumerate(self.ENHANCED_SEARCH_KEYWORDS[:max_attempts]):
            query = keyword_template.format(name=stock_name, code=stock_code)

            logger.info(f"[增强搜索] 第 {i + 1}/{max_attempts} 次搜索: {query}")

            # 依次尝试各个搜索引擎
            for provider in self._providers:
                if not provider.is_available:
                    continue

                try:
                    response = provider.search(query, max_results=3)

                    if response.success and response.results:
                        # 去重并添加结果
                        for result in response.results:
                            if result.url not in seen_urls:
                                seen_urls.add(result.url)
                                all_results.append(result)

                        if provider.name not in successful_providers:
                            successful_providers.append(provider.name)

                        logger.info(f"[增强搜索] {provider.name} 返回 {len(response.results)} 条结果")
                        break

                except Exception as e:
                    logger.warning(f"[增强搜索] {provider.name} 搜索异常: {e}")
                    continue

            # 短暂延迟避免请求过快
            if i < max_attempts - 1:
                time.sleep(0.5)

        # 汇总结果
        if all_results:
            final_results = all_results[:max_results]
            provider_str = ", ".join(successful_providers) if successful_providers else "None"

            logger.info(f"[增强搜索] 完成，共获取 {len(final_results)} 条结果（来源: {provider_str}）")

            return SearchResponse(
                query=f"{stock_name}({stock_code}) 股价走势",
                results=final_results,
                provider=provider_str,
                success=True,
            )
        else:
            logger.warning("[增强搜索] 所有搜索均未返回结果")
            return SearchResponse(
                query=f"{stock_name}({stock_code}) 股价走势",
                results=[],
                provider="None",
                success=False,
                error_message="增强搜索未找到相关信息",
            )

    def search_single_query(self, query: str, max_results: int = 10) -> dict[str, Any] | None:
        """
        执行单次搜索查询

        Args:
            query: 搜索关键词
            max_results: 最大结果数

        Returns:
            dict[str, Any] | None: 搜索结果字典，失败返回 None
        """
        # 依次尝试各个搜索引擎
        for provider in self._providers:
            if not provider.is_available:
                continue

            try:
                response = provider.search(query, max_results)

                if response.success and response.results:
                    # 转换为字典格式返回
                    return {
                        "query": response.query,
                        "results": [
                            {
                                "title": r.title,
                                "snippet": r.snippet,
                                "url": r.url,
                                "published_date": r.published_date,
                            }
                            for r in response.results
                        ],
                        "provider": response.provider,
                        "success": response.success,
                    }
            except Exception as e:
                logger.warning(f"[单次搜索] {provider.name} 搜索异常: {e}")
                continue

        # 所有引擎都失败
        logger.warning(f"[单次搜索] 所有搜索引擎都失败: {query}")
        return None


# === 便捷函数 ===
_search_service: SearchService | None = None


def get_search_service() -> SearchService:
    """获取搜索服务单例"""
    global _search_service

    if _search_service is None:
        from stock_analyzer.config import get_config

        config = get_config()

        _search_service = SearchService(
            bocha_keys=config.search.bocha_api_keys,
            tavily_keys=config.search.tavily_api_keys,
            brave_keys=config.search.brave_api_keys,
            serpapi_keys=config.search.serpapi_keys,
        )

    return _search_service


def reset_search_service() -> None:
    """重置搜索服务（用于测试）"""
    global _search_service
    _search_service = None
