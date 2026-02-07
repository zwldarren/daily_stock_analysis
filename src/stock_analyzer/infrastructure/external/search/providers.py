"""
搜索引擎提供者

实现各种搜索引擎的提供者
"""

import logging
import time
from abc import ABC, abstractmethod
from itertools import cycle
from urllib.parse import urlparse

import requests

from stock_analyzer.domain.models import SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class BaseSearchProvider(ABC):
    """搜索引擎基类"""

    def __init__(self, api_keys: list[str], name: str):
        """
        初始化搜索引擎

        Args:
            api_keys: API Key 列表（支持多个 key 负载均衡）
            name: 搜索引擎名称
        """
        self._api_keys = api_keys
        self._name = name
        self._key_cycle = cycle(api_keys) if api_keys else None
        self._key_usage: dict[str, int] = {key: 0 for key in api_keys}
        self._key_errors: dict[str, int] = {key: 0 for key in api_keys}

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        """检查是否有可用的 API Key"""
        return bool(self._api_keys)

    def _get_next_key(self) -> str | None:
        """
        获取下一个可用的 API Key（负载均衡）

        策略：轮询 + 跳过错误过多的 key
        """
        if not self._key_cycle:
            return None

        # 最多尝试所有 key
        for _ in range(len(self._api_keys)):
            key = next(self._key_cycle)
            # 跳过错误次数过多的 key（超过 3 次）
            if self._key_errors.get(key, 0) < 3:
                return key

        # 所有 key 都有问题，重置错误计数并返回第一个
        logger.warning(f"[{self._name}] 所有 API Key 都有错误记录，重置错误计数")
        self._key_errors = {key: 0 for key in self._api_keys}
        return self._api_keys[0] if self._api_keys else None

    def _record_success(self, key: str) -> None:
        """记录成功使用"""
        self._key_usage[key] = self._key_usage.get(key, 0) + 1
        # 成功后减少错误计数
        if key in self._key_errors and self._key_errors[key] > 0:
            self._key_errors[key] -= 1

    def _record_error(self, key: str) -> None:
        """记录错误"""
        self._key_errors[key] = self._key_errors.get(key, 0) + 1
        logger.warning(f"[{self._name}] API Key {key[:8]}... 错误计数: {self._key_errors[key]}")

    @abstractmethod
    def _do_search(self, query: str, api_key: str, max_results: int, days: int = 7) -> SearchResponse:
        """执行搜索（子类实现）"""
        pass

    def search(self, query: str, max_results: int = 5, days: int = 7) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            days: 搜索最近几天的时间范围（默认7天）

        Returns:
            SearchResponse 对象
        """
        api_key = self._get_next_key()
        if not api_key:
            return SearchResponse(
                query=query,
                results=[],
                provider=self._name,
                success=False,
                error_message=f"{self._name} 未配置 API Key",
            )

        start_time = time.time()
        try:
            response = self._do_search(query, api_key, max_results, days=days)
            response.search_time = time.time() - start_time

            if response.success:
                self._record_success(api_key)
                logger.info(
                    f"[{self._name}] 搜索 '{query}' 成功，"
                    f"返回 {len(response.results)} 条结果，"
                    f"耗时 {response.search_time:.2f}s"
                )
            else:
                self._record_error(api_key)

            return response

        except Exception as e:
            self._record_error(api_key)
            elapsed = time.time() - start_time
            logger.error(f"[{self._name}] 搜索 '{query}' 失败: {e}")
            return SearchResponse(
                query=query,
                results=[],
                provider=self._name,
                success=False,
                error_message=str(e),
                search_time=elapsed,
            )


class TavilySearchProvider(BaseSearchProvider):
    """
    Tavily 搜索引擎

    特点：
    - 专为 AI/LLM 优化的搜索 API
    - 免费版每月 1000 次请求
    - 返回结构化的搜索结果
    """

    def __init__(self, api_keys: list[str]):
        super().__init__(api_keys, "Tavily")

    def _do_search(self, query: str, api_key: str, max_results: int, days: int = 7) -> SearchResponse:
        """执行 Tavily 搜索"""
        try:
            from tavily import TavilyClient
        except ImportError:
            return SearchResponse(
                query=query,
                results=[],
                provider=self.name,
                success=False,
                error_message="tavily-python 未安装，请运行: pip install tavily-python",
            )

        try:
            client = TavilyClient(api_key=api_key)

            # 执行搜索
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
                days=days,
            )

            # 解析结果
            results = []
            for item in response.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        snippet=item.get("content", "")[:500],
                        url=item.get("url", ""),
                        source=self._extract_domain(item.get("url", "")),
                        published_date=item.get("published_date"),
                    )
                )

            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                success=True,
            )

        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                error_msg = f"API 配额已用尽: {error_msg}"

            return SearchResponse(query=query, results=[], provider=self.name, success=False, error_message=error_msg)

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从 URL 提取域名作为来源"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain or "未知来源"
        except Exception:
            return "未知来源"


class SerpAPISearchProvider(BaseSearchProvider):
    """
    SerpAPI 搜索引擎

    特点：
    - 支持 Google、Bing、百度等多种搜索引擎
    - 免费版每月 100 次请求
    """

    def __init__(self, api_keys: list[str]):
        super().__init__(api_keys, "SerpAPI")

    def _do_search(self, query: str, api_key: str, max_results: int, days: int = 7) -> SearchResponse:
        """执行 SerpAPI 搜索"""
        try:
            from serpapi import GoogleSearch
        except ImportError:
            return SearchResponse(
                query=query,
                results=[],
                provider=self.name,
                success=False,
                error_message="google-search-results 未安装，请运行: pip install google-search-results",
            )

        try:
            # 确定时间范围参数 tbs
            tbs = "qdr:w"
            if days <= 1:
                tbs = "qdr:d"
            elif days <= 7:
                tbs = "qdr:w"
            elif days <= 30:
                tbs = "qdr:m"
            else:
                tbs = "qdr:y"

            # 使用 Google 搜索
            params = {
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "google_domain": "google.com.hk",
                "hl": "zh-cn",
                "gl": "cn",
                "tbs": tbs,
                "num": max_results,
            }

            search = GoogleSearch(params)
            response = search.get_dict()

            # 解析结果
            results = []

            # 1. 解析 Knowledge Graph
            kg = response.get("knowledge_graph", {})
            if kg:
                title = kg.get("title", "知识图谱")
                desc = kg.get("description", "")

                details = []
                for key in ["type", "founded", "headquarters", "employees", "ceo"]:
                    val = kg.get(key)
                    if val:
                        details.append(f"{key}: {val}")

                snippet = f"{desc}\n" + " | ".join(details) if details else desc

                results.append(
                    SearchResult(
                        title=f"[知识图谱] {title}",
                        snippet=snippet,
                        url=kg.get("source", {}).get("link", ""),
                        source="Google Knowledge Graph",
                    )
                )

            # 2. 解析 Organic Results
            organic_results = response.get("organic_results", [])

            for item in organic_results[:max_results]:
                link = item.get("link", "")
                snippet = item.get("snippet", "")

                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        snippet=snippet[:1000],
                        url=link,
                        source=item.get("source", self._extract_domain(link)),
                        published_date=item.get("date"),
                    )
                )

            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                success=True,
            )

        except Exception as e:
            error_msg = str(e)
            return SearchResponse(query=query, results=[], provider=self.name, success=False, error_message=error_msg)

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从 URL 提取域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "") or "未知来源"
        except Exception:
            return "未知来源"


class BraveSearchProvider(BaseSearchProvider):
    """
    Brave Search 搜索引擎

    特点：
    - 隐私优先的独立搜索引擎
    - 索引超过300亿页面
    - 免费层可用
    - 支持时间范围过滤

    文档：https://brave.com/search/api/
    """

    API_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_keys: list[str]):
        super().__init__(api_keys, "Brave")

    def _do_search(self, query: str, api_key: str, max_results: int, days: int = 7) -> SearchResponse:
        """执行 Brave 搜索"""
        try:
            # 请求头
            headers = {"X-Subscription-Token": api_key, "Accept": "application/json"}

            # 确定时间范围（freshness 参数）
            if days <= 1:
                freshness = "pd"  # Past day (24小时)
            elif days <= 7:
                freshness = "pw"  # Past week
            elif days <= 30:
                freshness = "pm"  # Past month
            else:
                freshness = "py"  # Past year

            # 请求参数
            params = {
                "q": query,
                "count": min(max_results, 20),  # Brave 最大支持20条
                "freshness": freshness,
                "search_lang": "en",  # 英文内容（US股票优先）
                "country": "US",  # 美国区域偏好
                "safesearch": "moderate",
            }

            # 执行搜索（GET 请求）
            response = requests.get(self.API_ENDPOINT, headers=headers, params=params, timeout=10)

            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = self._parse_error(response)
                logger.warning(f"[Brave] 搜索失败: {error_msg}")
                return SearchResponse(
                    query=query, results=[], provider=self.name, success=False, error_message=error_msg
                )

            # 解析响应
            try:
                data = response.json()
            except ValueError as e:
                error_msg = f"响应JSON解析失败: {str(e)}"
                logger.error(f"[Brave] {error_msg}")
                return SearchResponse(
                    query=query, results=[], provider=self.name, success=False, error_message=error_msg
                )

            logger.info(f"[Brave] 搜索完成，query='{query}'")
            logger.debug(f"[Brave] 原始响应: {data}")

            # 解析搜索结果
            results = []
            web_data = data.get("web", {})
            web_results = web_data.get("results", [])

            for item in web_results[:max_results]:
                # 解析发布日期（ISO 8601 格式）
                published_date = None
                age = item.get("age") or item.get("page_age")
                if age:
                    try:
                        # 转换 ISO 格式为简单日期字符串
                        from datetime import datetime

                        dt = datetime.fromisoformat(age.replace("Z", "+00:00"))
                        published_date = dt.strftime("%Y-%m-%d")
                    except ValueError, AttributeError:
                        published_date = age  # 解析失败时使用原始值

                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        snippet=item.get("description", "")[:500],  # 截取到500字符
                        url=item.get("url", ""),
                        source=self._extract_domain(item.get("url", "")),
                        published_date=published_date,
                    )
                )

            logger.info(f"[Brave] 成功解析 {len(results)} 条结果")

            return SearchResponse(query=query, results=results, provider=self.name, success=True)

        except requests.exceptions.Timeout:
            error_msg = "请求超时"
            logger.error(f"[Brave] {error_msg}")
            return SearchResponse(query=query, results=[], provider=self.name, success=False, error_message=error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(f"[Brave] {error_msg}")
            return SearchResponse(query=query, results=[], provider=self.name, success=False, error_message=error_msg)
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(f"[Brave] {error_msg}")
            return SearchResponse(query=query, results=[], provider=self.name, success=False, error_message=error_msg)

    def _parse_error(self, response) -> str:
        """解析错误响应"""
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                # Brave API 返回的错误格式
                if "message" in error_data:
                    return error_data["message"]
                if "error" in error_data:
                    return error_data["error"]
                return str(error_data)
            return response.text[:200]
        except Exception:
            return f"HTTP {response.status_code}: {response.text[:200]}"

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从 URL 提取域名作为来源"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain or "未知来源"
        except Exception:
            return "未知来源"


class BochaSearchProvider(BaseSearchProvider):
    """
    博查搜索引擎

    特点：
    - 专为AI优化的中文搜索API
    - 结果准确、摘要完整
    - 支持时间范围过滤和AI摘要
    """

    def __init__(self, api_keys: list[str]):
        super().__init__(api_keys, "Bocha")

    def _do_search(self, query: str, api_key: str, max_results: int, days: int = 7) -> SearchResponse:
        """执行博查搜索"""
        try:
            # 确定时间范围
            freshness = "oneWeek"
            if days <= 1:
                freshness = "oneDay"
            elif days <= 7:
                freshness = "oneWeek"
            elif days <= 30:
                freshness = "oneMonth"
            else:
                freshness = "oneYear"

            # 请求参数
            payload = {
                "query": query,
                "freshness": freshness,
                "summary": True,
                "count": min(max_results, 50),
            }

            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            # 执行搜索
            response = requests.post(
                "https://api.bocha.cn/v1/web-search",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code != 200:
                error_message = response.text
                if response.status_code == 403:
                    error_msg = f"余额不足: {error_message}"
                elif response.status_code == 401:
                    error_msg = f"API KEY无效: {error_message}"
                elif response.status_code == 429:
                    error_msg = f"请求频率达到限制: {error_message}"
                else:
                    error_msg = f"HTTP {response.status_code}: {error_message}"

                return SearchResponse(
                    query=query,
                    results=[],
                    provider=self.name,
                    success=False,
                    error_message=error_msg,
                )

            data = response.json()

            if data.get("code") != 200:
                error_msg = data.get("msg") or f"API返回错误码: {data.get('code')}"
                return SearchResponse(
                    query=query,
                    results=[],
                    provider=self.name,
                    success=False,
                    error_message=error_msg,
                )

            # 解析搜索结果
            results = []
            web_pages = data.get("data", {}).get("webPages", {})
            value_list = web_pages.get("value", [])

            for item in value_list[:max_results]:
                snippet = item.get("summary") or item.get("snippet", "")
                if snippet:
                    snippet = snippet[:500]

                results.append(
                    SearchResult(
                        title=item.get("name", ""),
                        snippet=snippet,
                        url=item.get("url", ""),
                        source=item.get("siteName") or self._extract_domain(item.get("url", "")),
                        published_date=item.get("datePublished"),
                    )
                )

            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                success=True,
            )

        except requests.exceptions.Timeout:
            return SearchResponse(query=query, results=[], provider=self.name, success=False, error_message="请求超时")
        except requests.exceptions.RequestException as e:
            return SearchResponse(
                query=query, results=[], provider=self.name, success=False, error_message=f"网络请求失败: {str(e)}"
            )
        except Exception as e:
            return SearchResponse(
                query=query, results=[], provider=self.name, success=False, error_message=f"未知错误: {str(e)}"
            )

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从 URL 提取域名作为来源"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain or "未知来源"
        except Exception:
            return "未知来源"
