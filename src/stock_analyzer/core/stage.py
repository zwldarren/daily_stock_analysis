"""
流水线阶段基类模块

提供 Stage 模式的抽象接口，支持 Pipeline 的模块化和可扩展设计。
"""

from abc import ABC, abstractmethod
from typing import Any


class PipelineStage[T, R](ABC):
    """流水线阶段基类

    定义流水线中每个处理阶段的标准接口，支持：
    - 正向执行（execute）
    - 失败回滚（rollback，可选）

    类型参数：
        T: 输入数据类型
        R: 输出数据类型

    Example:
        >>> class DataCollectionStage(PipelineStage[str, StageContext]):
        ...     def execute(self, stock_code: str) -> StageContext:
        ...         context = StageContext()
        ...         context.set("stock_code", stock_code)
        ...         return context
    """

    @abstractmethod
    def execute(self, input_data: T) -> R:
        """执行阶段

        Args:
            input_data: 输入数据

        Returns:
            处理结果

        Raises:
            StageExecutionError: 阶段执行失败时抛出
        """
        pass

    # Note: rollback is intentionally not abstract - it's optional for subclasses
    def rollback(self, input_data: T) -> None:  # noqa: B027
        """回滚阶段（可选）

        当流水线执行失败时，会按逆序调用各阶段的 rollback 方法。
        子类可以重写此方法实现自定义回滚逻辑。

        Args:
            input_data: 输入数据（execute 接收的同一对象）
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class StageContext:
    """阶段上下文

    在流水线各阶段之间传递数据，支持：
    - 存储任意类型的中间结果
    - 记录元数据（如执行时间、数据来源等）
    - 类型安全的数据访问

    Example:
        >>> context = StageContext()
        >>> context.set("stock_code", "600519")
        >>> context.set("raw_data", df)
        >>> code = context.get("stock_code")
        >>> data = context.get("raw_data")
    """

    def __init__(self):
        self.data: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """设置数据

        Args:
            key: 数据键
            value: 数据值
        """
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取数据

        Args:
            key: 数据键
            default: 默认值（如果键不存在）

        Returns:
            存储的值或默认值
        """
        return self.data.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据

        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据

        Args:
            key: 元数据键
            default: 默认值（如果键不存在）

        Returns:
            存储的元数据或默认值
        """
        return self.metadata.get(key, default)

    def has(self, key: str) -> bool:
        """检查是否存在指定键的数据

        Args:
            key: 数据键

        Returns:
            是否存在
        """
        return key in self.data

    def remove(self, key: str) -> None:
        """删除指定键的数据

        Args:
            key: 数据键
        """
        if key in self.data:
            del self.data[key]

    def clear(self) -> None:
        """清空所有数据"""
        self.data.clear()
        self.metadata.clear()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于序列化）

        Returns:
            包含 data 和 metadata 的字典
        """
        return {"data": self.data, "metadata": self.metadata}

    def __repr__(self) -> str:
        return f"StageContext(data_keys={list(self.data.keys())}, metadata_keys={list(self.metadata.keys())})"


class StageExecutionError(Exception):
    """阶段执行错误

    当 PipelineStage 执行失败时抛出，包含错误上下文信息。
    """

    def __init__(self, stage_name: str, message: str, cause: Exception | None = None):
        self.stage_name = stage_name
        self.cause = cause
        super().__init__(f"Stage '{stage_name}' execution failed: {message}")

    def __str__(self) -> str:
        if self.cause:
            return f"{super().__str__()} (caused by {type(self.cause).__name__}: {self.cause})"
        return super().__str__()
