"""Repositories for the stock analyzer application.

This module contains the implementation of the repositories that
interact with the database to perform CRUD operations on stock data.
"""

from stock_analyzer.infrastructure.persistence.repositories.stock_repository import StockRepository

__all__ = ["StockRepository"]
