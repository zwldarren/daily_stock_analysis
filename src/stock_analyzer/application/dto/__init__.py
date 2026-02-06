"""
数据传输对象 (DTO)

定义应用层与外部交互的数据结构
"""

from stock_analyzer.application.dto.analysis_dto import (
    AnalysisRequestDTO,
    AnalysisResponseDTO,
    StockContextDTO,
)

__all__ = [
    "AnalysisRequestDTO",
    "AnalysisResponseDTO",
    "StockContextDTO",
]
