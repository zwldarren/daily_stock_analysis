"""
领域事件基础框架

提供领域事件的定义和事件总线机制。
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import suppress
from typing import Any


class DomainEvent(ABC):
    """
    领域事件基类

    所有领域事件都应继承此类，使用不可变数据类实现。
    领域事件表示领域中发生的、有业务意义的事情。

    特性：
    - 不可变（frozen=True）
    - 自动记录发生时间
    - 可被事件总线分发和处理

    子类示例：
        @dataclass(frozen=True)
        class StockAnalyzed(DomainEvent):
            stock_code: str
            analysis_result: Any
            timestamp: datetime = field(default_factory=datetime.now)

            @property
            def event_type(self) -> str:
                return "stock_analyzed"
    """

    @property
    @abstractmethod
    def event_type(self) -> str:
        """返回事件类型标识（子类必须实现）"""
        pass


class EventBus:
    """
    事件总线

    职责：
    1. 管理事件处理器注册
    2. 分发领域事件给所有注册的处理器
    3. 支持同步和异步事件处理

    使用示例：
        # 定义处理器
        def on_stock_analyzed(event: StockAnalyzed):
            print(f"股票 {event.stock_code} 分析完成")

        # 注册处理器
        event_bus.subscribe("stock_analyzed", on_stock_analyzed)

        # 发布事件
        event = StockAnalyzed(stock_code="000001", ...)
        event_bus.publish(event)
    """

    def __init__(self) -> None:
        """初始化事件总线"""
        self._handlers: dict[str, list[Callable[[Any], Any]]] = {}

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Any], Any],
    ) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型标识
            handler: 事件处理函数（接收 DomainEvent 子类）
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Any], Any],
    ) -> None:
        """
        取消订阅事件

        Args:
            event_type: 事件类型标识
            handler: 要移除的处理函数
        """
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    def publish(self, event: DomainEvent) -> None:
        """
        发布事件

        同步调用所有注册的处理器。

        Args:
            event: 要发布的领域事件
        """
        event_type = event.event_type

        if event_type not in self._handlers:
            return

        for handler in self._handlers[event_type]:
            with suppress(Exception):
                # 事件处理失败不应影响其他处理器
                # 日志记录由处理器自行处理
                handler(event)

    def clear_handlers(self, event_type: str | None = None) -> None:
        """
        清除事件处理器

        Args:
            event_type: 要清除的事件类型，None 表示清除所有
        """
        if event_type is None:
            self._handlers.clear()
        elif event_type in self._handlers:
            del self._handlers[event_type]


# 全局事件总线实例
event_bus = EventBus()
