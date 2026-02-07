"""
AI客户端模块

封装各种AI API客户端的初始化和调用逻辑
"""

import logging
import time
from typing import Any

from stock_analyzer.ai.prompts import SYSTEM_PROMPT
from stock_analyzer.config import get_config
from stock_analyzer.utils import calculate_backoff_delay

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini API客户端封装"""

    def __init__(self, api_key: str | None = None):
        """
        初始化Gemini客户端

        Args:
            api_key: Gemini API Key（可选，默认从配置读取）
        """
        config = get_config()
        self._api_key = api_key or config.ai.gemini_api_key
        self._genai_client = None
        self._current_model_name = None
        self._using_fallback = False

        # 检查API Key是否有效
        if self._api_key and not self._api_key.startswith("your_") and len(self._api_key) > 10:
            self._init_client()

    def _init_client(self) -> None:
        """初始化Gemini客户端"""
        try:
            from google import genai
            from google.genai import types

            config = get_config()
            model_name = config.ai.gemini_model
            fallback_model = config.ai.gemini_model_fallback

            self._genai_client = genai.Client(api_key=self._api_key)

            # 尝试初始化主模型
            try:
                self._genai_client.models.generate_content(
                    model=model_name,
                    contents="test",
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.5,
                        max_output_tokens=10,
                    ),
                )
                self._current_model_name = model_name
                self._using_fallback = False
                logger.info(f"Gemini 模型初始化成功 (模型: {model_name})")
            except Exception as model_error:
                logger.warning(f"主模型 {model_name} 初始化失败: {model_error}，尝试备选模型 {fallback_model}")
                self._genai_client.models.generate_content(
                    model=fallback_model,
                    contents="test",
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.5,
                        max_output_tokens=10,
                    ),
                )
                self._current_model_name = fallback_model
                self._using_fallback = True
                logger.info(f"Gemini 备选模型初始化成功 (模型: {fallback_model})")

        except Exception as e:
            logger.error(f"Gemini 模型初始化失败: {e}")
            self._genai_client = None

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._genai_client is not None

    def switch_to_fallback(self) -> bool:
        """切换到备选模型"""
        try:
            from google.genai import types

            config = get_config()
            fallback_model = config.ai.gemini_model_fallback

            if not self._genai_client:
                logger.error("[LLM] Gemini client not initialized")
                return False

            logger.warning(f"[LLM] 切换到备选模型: {fallback_model}")
            self._genai_client.models.generate_content(
                model=fallback_model,
                contents="test",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.5,
                    max_output_tokens=10,
                ),
            )
            self._current_model_name = fallback_model
            self._using_fallback = True
            logger.info(f"[LLM] 备选模型 {fallback_model} 初始化成功")
            return True
        except Exception as e:
            logger.error(f"[LLM] 切换备选模型失败: {e}")
            return False

    def generate(self, prompt: str, generation_config: dict) -> str:
        """
        生成内容，带重试机制

        Args:
            prompt: 提示词
            generation_config: 生成配置

        Returns:
            生成的文本
        """
        from google.genai import types

        config = get_config()
        max_retries = config.ai.gemini_max_retries
        base_delay = config.ai.gemini_retry_delay

        if not self._genai_client:
            raise Exception("Gemini client is not initialized")

        current_model = self._current_model_name
        if not current_model:
            raise Exception("Gemini model name is not set")

        tried_fallback = self._using_fallback

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = calculate_backoff_delay(attempt, base_delay, max_delay=60.0)
                    logger.info(f"[Gemini] 第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                    time.sleep(delay)

                response = self._genai_client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=generation_config.get("temperature", 0.5),
                        max_output_tokens=generation_config.get("max_output_tokens", 8192),
                    ),
                )

                if response and response.text:
                    return response.text
                else:
                    raise ValueError("Gemini 返回空响应")

            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower()

                if is_rate_limit:
                    logger.warning(f"[Gemini] API 限流 (429)，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")

                    if attempt >= max_retries // 2 and not tried_fallback:
                        if self.switch_to_fallback():
                            tried_fallback = True
                            logger.info("[Gemini] 已切换到备选模型，继续重试")
                        else:
                            logger.warning("[Gemini] 切换备选模型失败，继续使用当前模型重试")
                else:
                    logger.warning(f"[Gemini] API 调用失败，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")

        raise Exception("Gemini API 调用失败，已达最大重试次数")


class OpenAIClient:
    """OpenAI兼容API客户端封装"""

    def __init__(self):
        """初始化OpenAI兼容客户端"""
        self._client = None
        self._current_model_name = None
        self._token_param_mode: dict[str, str | None] = {}
        self._init_client()

    def _init_client(self) -> None:
        """初始化OpenAI兼容客户端"""
        config = get_config()

        openai_key_valid = (
            config.ai.openai_api_key
            and not config.ai.openai_api_key.startswith("your_")
            and len(config.ai.openai_api_key) > 10
        )

        if not openai_key_valid:
            logger.debug("OpenAI 兼容 API 未配置或配置无效")
            return

        try:
            from openai import OpenAI
        except ImportError:
            logger.error("未安装 openai 库，请运行: pip install openai")
            return

        try:
            client_kwargs: dict[str, Any] = {"api_key": config.ai.openai_api_key or ""}
            if config.ai.openai_base_url and config.ai.openai_base_url.startswith("http"):
                client_kwargs["base_url"] = config.ai.openai_base_url

            self._client = OpenAI(**client_kwargs)
            self._current_model_name = config.ai.openai_model
            logger.info(
                f"OpenAI 兼容 API 初始化成功 (base_url: {config.ai.openai_base_url}, model: {config.ai.openai_model})"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "socks" in error_msg or "socksio" in error_msg or "proxy" in error_msg:
                logger.error(f"OpenAI 代理配置错误: {e}，如使用 SOCKS 代理请运行: pip install httpx[socks]")
            else:
                logger.error(f"OpenAI 兼容 API 初始化失败: {e}")

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._client is not None

    def generate(self, prompt: str, generation_config: dict) -> str:
        """
        生成内容，带重试机制

        Args:
            prompt: 提示词
            generation_config: 生成配置

        Returns:
            生成的文本
        """
        config = get_config()
        max_retries = config.ai.gemini_max_retries
        base_delay = config.ai.gemini_retry_delay

        if not self._client:
            raise Exception("OpenAI client is not initialized")

        if not self._current_model_name:
            raise Exception("OpenAI model name is not set")

        model_name = self._current_model_name
        mode = self._token_param_mode.get(model_name, "max_tokens")
        max_output_tokens = generation_config.get("max_output_tokens", 8192)

        def _build_base_request_kwargs() -> dict:
            kwargs = {
                "model": self._current_model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": generation_config.get("temperature", config.ai.openai_temperature),
            }
            return kwargs

        def _is_unsupported_param_error(error_message: str, param_name: str) -> bool:
            lower_msg = error_message.lower()
            return (
                "400" in lower_msg or "unsupported parameter" in lower_msg or "unsupported param" in lower_msg
            ) and param_name in lower_msg

        def _kwargs_with_mode(mode_value):
            kwargs = _build_base_request_kwargs()
            if mode_value is not None:
                kwargs[mode_value] = max_output_tokens
            return kwargs

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = calculate_backoff_delay(attempt, base_delay, max_delay=60.0)
                    logger.info(f"[OpenAI] 第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                    time.sleep(delay)

                try:
                    response = self._client.chat.completions.create(**_kwargs_with_mode(mode))
                except Exception as e:
                    error_str = str(e)
                    if mode == "max_tokens" and _is_unsupported_param_error(error_str, "max_tokens"):
                        mode = "max_completion_tokens"
                        self._token_param_mode[model_name] = mode
                        response = self._client.chat.completions.create(**_kwargs_with_mode(mode))
                    elif mode == "max_completion_tokens" and _is_unsupported_param_error(
                        error_str, "max_completion_tokens"
                    ):
                        mode = None
                        self._token_param_mode[model_name] = mode
                        response = self._client.chat.completions.create(**_kwargs_with_mode(mode))
                    else:
                        raise

                if response and response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
                else:
                    raise ValueError("OpenAI API 返回空响应")

            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower()

                if is_rate_limit:
                    logger.warning(f"[OpenAI] API 限流，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")
                else:
                    logger.warning(f"[OpenAI] API 调用失败，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")

                if attempt == max_retries - 1:
                    raise

        raise Exception("OpenAI API 调用失败，已达最大重试次数")
