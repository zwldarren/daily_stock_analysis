"""
领域层异常定义

定义清晰的异常体系，便于错误处理和调试
"""


class StockAnalyzerException(Exception):
    """基础异常类"""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class DataFetchError(StockAnalyzerException):
    """数据获取失败"""

    pass


class StorageError(StockAnalyzerException):
    """数据存储失败"""

    pass


class ValidationError(StockAnalyzerException):
    """数据验证失败"""

    pass


class AnalysisError(StockAnalyzerException):
    """分析过程错误"""

    pass


class NotificationError(StockAnalyzerException):
    """通知发送失败"""

    pass


class ConfigurationError(StockAnalyzerException):
    """配置错误"""

    pass
