"""
回退策略模式

提供统一的错误处理和回退机制，用于数据源、AI 客户端等需要故障转移的场景。
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class FallbackStrategy[T](ABC):
    """
    回退策略抽象基类

    定义统一的故障转移接口，支持多种回退策略实现。
    """

    @abstractmethod
    def execute(self, operation: Callable[[], T], fallback_chain: list[Callable[[], T]]) -> T:
        """
        执行操作，失败时按顺序尝试回退方案

        Args:
            operation: 主操作
            fallback_chain: 回退操作链

        Returns:
            操作结果

        Raises:
            Exception: 所有操作都失败时抛出最后一个异常
        """
        pass


class SequentialFallbackStrategy[T]:
    """
    顺序回退策略

    按顺序尝试主操作和回退操作，直到成功或全部失败。
    适用于数据源切换、AI 客户端回退等场景。
    """

    def __init__(self, max_retries: int = 1, name: str = "default"):
        self._max_retries = max_retries
        self._name = name

    def execute(self, operation: Callable[[], T], fallback_chain: list[Callable[[], T]]) -> T:
        """
        顺序执行操作链

        Args:
            operation: 主操作
            fallback_chain: 回退操作链

        Returns:
            操作结果
        """
        operations = [operation] + fallback_chain
        last_error = None

        for i, op in enumerate(operations):
            op_name = op.__name__ if hasattr(op, "__name__") else f"operation_{i}"

            for attempt in range(self._max_retries):
                try:
                    result = op()
                    if i > 0:
                        logger.info(f"[{self._name}] 回退成功: 使用 {op_name}")
                    return result
                except Exception as e:
                    last_error = e
                    logger.warning(f"[{self._name}] {op_name} 失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")

        # 所有操作都失败
        error_msg = f"[{self._name}] 所有操作都失败，尝试了 {len(operations)} 个操作"
        logger.error(error_msg)
        if last_error:
            raise last_error
        raise Exception(error_msg)


class CircuitBreakerFallbackStrategy[T]:
    """
    熔断回退策略

    当主操作连续失败达到一定阈值时，直接切换到回退操作。
    适用于需要快速故障转移的场景。
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
        name: str = "circuit_breaker",
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._name = name
        self._failure_count = 0
        self._last_failure_time = None
        self._is_open = False

    def execute(self, operation: Callable[[], T], fallback_chain: list[Callable[[], T]]) -> T:
        """
        执行操作，支持熔断机制

        Args:
            operation: 主操作
            fallback_chain: 回退操作链

        Returns:
            操作结果
        """
        from datetime import datetime

        # 检查熔断状态
        if self._is_open and self._last_failure_time:
            elapsed = (datetime.now() - self._last_failure_time).total_seconds()
            if elapsed > self._recovery_timeout:
                logger.info(f"[{self._name}] 熔断恢复，尝试主操作")
                self._is_open = False
                self._failure_count = 0
            else:
                logger.debug(f"[{self._name}] 熔断开启，跳过主操作")
                return self._execute_fallback(fallback_chain)

        # 尝试主操作
        try:
            result = operation()
            # 成功则重置失败计数
            if self._failure_count > 0:
                logger.info(f"[{self._name}] 主操作恢复成功")
            self._failure_count = 0
            self._is_open = False
            return result
        except Exception as e:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._failure_count >= self._failure_threshold:
                self._is_open = True
                logger.warning(f"[{self._name}] 熔断开启: 连续失败 {self._failure_count} 次")

            logger.warning(f"[{self._name}] 主操作失败: {e}")
            return self._execute_fallback(fallback_chain)

    def _execute_fallback(self, fallback_chain: list[Callable[[], T]]) -> T:
        """执行回退链"""
        last_error = None

        for i, fallback in enumerate(fallback_chain):
            fallback_name = fallback.__name__ if hasattr(fallback, "__name__") else f"fallback_{i}"

            try:
                result = fallback()
                logger.info(f"[{self._name}] 回退成功: 使用 {fallback_name}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"[{self._name}] 回退 {fallback_name} 失败: {e}")

        if last_error:
            raise last_error
        raise Exception(f"[{self._name}] 所有回退操作都失败")


class FallbackManager:
    """
    回退管理器

    提供便捷的方法来使用回退策略。
    """

    def __init__(self, strategy: Any | None = None):
        self._strategy = strategy or SequentialFallbackStrategy[Any]()

    def execute(self, operation: Callable[[], Any], *fallbacks: Callable[[], Any]) -> Any:
        """
        执行操作，失败时尝试回退

        Args:
            operation: 主操作
            *fallbacks: 可变数量的回退操作

        Returns:
            操作结果
        """
        return self._strategy.execute(operation, list(fallbacks))

    def with_strategy(self, strategy: FallbackStrategy[Any]) -> FallbackManager:
        """
        切换策略并返回新的管理器实例

        Args:
            strategy: 新的回退策略

        Returns:
            配置了指定策略的管理器实例
        """
        return FallbackManager(strategy)


def with_fallback(*fallbacks: Callable[[], Any]) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    装饰器风格的回退执行

    使用示例:
        def fetch_from_source_a():
            return fetch_data("source_a")

        def fetch_from_source_b():
            return fetch_data("source_b")

        @with_fallback(fetch_from_source_b)
        def fetch_data():
            return fetch_from_source_a()

        result = fetch_data()
    """

    def decorator(operation: Callable[[], Any]) -> Callable[[], Any]:
        def wrapper() -> Any:
            manager: FallbackManager = FallbackManager()
            return manager.execute(operation, *fallbacks)

        return wrapper

    return decorator


def create_sequential_fallback(name: str = "sequential", max_retries: int = 1) -> FallbackManager:
    """创建顺序回退管理器"""
    strategy: SequentialFallbackStrategy[Any] = SequentialFallbackStrategy(max_retries=max_retries, name=name)
    return FallbackManager(strategy)


def create_circuit_breaker(
    name: str = "circuit_breaker",
    failure_threshold: int = 3,
    recovery_timeout: int = 60,
) -> FallbackManager:
    """创建熔断回退管理器"""
    strategy: CircuitBreakerFallbackStrategy[Any] = CircuitBreakerFallbackStrategy(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        name=name,
    )
    return FallbackManager(strategy)
