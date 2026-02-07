"""
AI客户端模块 - 基于 litellm 的统一实现

使用 litellm 支持 100+ LLM providers，统一接口格式
"""

import logging
import time
from typing import Any

import litellm
from litellm import completion

from stock_analyzer.ai.prompts import SYSTEM_PROMPT
from stock_analyzer.config import get_config
from stock_analyzer.utils import calculate_backoff_delay

logger = logging.getLogger(__name__)

# 配置 litellm 日志级别
litellm.set_verbose = False


class LiteLLMClient:
    """
    基于 litellm 的统一 LLM 客户端

    使用方式：
        client = LiteLLMClient("deepseek/deepseek-reasoner", api_key="sk-...")
        response = client.generate("分析这只股票", {"temperature": 0.7})
    """

    def __init__(
        self,
        model: str,
        api_key: str | None,
        base_url: str | None = None,
    ):
        """
        初始化 LiteLLM 客户端

        Args:
            model: 模型名称（litellm 格式：provider/model-name）
            api_key: API Key
            base_url: 自定义 base URL（可选，用于自托管或代理）
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

        # 验证配置有效性
        self._available = self._validate_config()

        if self._available:
            logger.info(f"LiteLLM 客户端初始化成功 (模型: {model})")
        else:
            logger.warning(f"LiteLLM 客户端初始化失败 (模型: {model}) - 配置无效")

    def _validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.api_key:
            return False
        if not self.model or "/" not in self.model:
            logger.warning(f"模型名称格式错误，应为 'provider/model-name' 格式: {self.model}")
            return False
        return True

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._available

    def generate(self, prompt: str, generation_config: dict) -> str:
        """
        生成内容，带重试机制

        Args:
            prompt: 用户提示词
            generation_config: 生成配置（temperature, max_tokens 等）

        Returns:
            生成的文本

        Raises:
            Exception: 当 API 调用失败且重试次数用尽时
        """
        if not self._available:
            raise Exception(f"LiteLLM 客户端未初始化或配置无效 (模型: {self.model})")

        config = get_config()
        max_retries = config.ai.llm_max_retries
        base_delay = config.ai.llm_retry_delay

        # 构建请求参数
        temperature = generation_config.get("temperature", config.ai.llm_temperature)
        max_tokens = generation_config.get("max_output_tokens", config.ai.llm_max_tokens)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = calculate_backoff_delay(attempt, base_delay, max_delay=60.0)
                    logger.info(f"[{self.model}] 第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                    time.sleep(delay)

                # 构建 litellm 调用参数
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                # 添加 API key（如果提供）
                if self.api_key:
                    kwargs["api_key"] = self.api_key

                # 添加自定义 base_url（如果提供）
                if self.base_url:
                    kwargs["api_base"] = self.base_url

                response = completion(**kwargs)

                # 提取生成的内容
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content:
                        return content.strip()

                raise ValueError(f"{self.model} 返回空响应")

            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower()

                if is_rate_limit:
                    logger.warning(f"[{self.model}] API 限流，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")
                else:
                    logger.warning(
                        f"[{self.model}] API 调用失败，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}"
                    )

                if attempt == max_retries - 1:
                    raise Exception(f"{self.model} API 调用失败，已达最大重试次数: {error_str}") from e

        raise Exception(f"{self.model} API 调用失败，已达最大重试次数") from None
