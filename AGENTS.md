# AGENTS.md - Agentic Coding Guidelines

## Build/Lint/Test Commands

### Installation & Environment
```bash
# Install dependencies
uv sync
```

### Lint, Format & Type Check
```bash
# Format code with ruff
ruff format

# Lint with ruff
ruff check --fix

# Type checking with ty
ty check
```

### Running the Application
```bash
# Use uv run to execute (entry point is stock-analyzer command)
uv run stock-analyzer --help                    # See all options
uv run stock-analyzer --stocks 600519           # Analyze single stock
uv run stock-analyzer --market-review           # Market review only
uv run stock-analyzer --dry-run --no-notify     # Test without AI/notifications
```

### Docker
```bash
# Build and run Docker container
docker build -t stock-analyzer -f docker/Dockerfile .
docker run -it --env-file .env stock-analyzer
```

## Code Style Guidelines

### Imports (enforced by ruff)
- **Order**: stdlib → third-party → local (with blank line separation)
- **Style**: Absolute imports preferred over relative
- **Example**:
  ```python
  import json
  import logging
  from dataclasses import dataclass
  from typing import Any

  import pandas as pd
  import requests
  from tenacity import retry, stop_after_attempt

  from stock_analyzer.config import get_config
  from stock_analyzer.data_provider.base import BaseFetcher
  ```

### Formatting & Linting (ruff)
- **Line length**: 120 characters (configured in pyproject.toml)
- **Quotes**: Double quotes for strings
- **Trailing commas**: Required for multi-line structures
- Use `ruff format` to auto-format and `ruff check` to lint

### Type Checking (ty)
- Run `ty check .` to validate type hints
- Use type hints for function parameters and return types
- `from typing import Any, Optional, Union`
- Use `dict`, `list` instead of `Dict`, `List` (Python 3.9+)

### Naming Conventions
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private methods: `_leading_underscore`

### Error Handling
- **Custom exceptions**: Extend `Exception` for domain-specific errors
  ```python
  class DataFetchError(Exception):
      """Raised when data fetching fails"""
      pass
  ```
- **Retry logic**: Use `tenacity` for transient failures
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
  def fetch_data():
      pass
  ```
- **Logging**: Use module-level logger
  ```python
  logger = logging.getLogger(__name__)
  logger.error("Failed to fetch data: %s", e)
  ```

### Architecture Patterns
- **Dataclasses**: Use for data structures
  ```python
  @dataclass
  class AnalysisResult:
      stock_code: str
      recommendation: str
      confidence: float
  ```
- **Base classes**: Abstract base classes for pluggable components
  - `BaseFetcher` in `data_provider/base.py`
  - Allows multiple data sources (AkShare, YFinance, etc.)
- **Configuration**: Centralized via `config.py` with `get_config()`

### Documentation
- **Docstrings**: Use triple quotes for modules, classes, and functions
- **Comments**: Chinese comments are acceptable (project is bilingual)
- **Keep it practical**: Focus on "why" not "what"

## AI/ML Patterns

- **API clients**: Support multiple providers (Gemini, OpenAI, DeepSeek)
- **JSON parsing**: Use `json_repair` for handling LLM output
- **Rate limiting**: Implement delays between API calls
- **Prompts**: Stored as constants, version controlled

## Common Tasks

```bash
# Add new data provider
# 1. Create file in src/stock_analyzer/data_provider/
# 2. Inherit from BaseFetcher
# 3. Implement required methods
# 4. Register in DataFetcherManager

# Test a single stock analysis
uv run stock-analyzer --stocks 600519 --no-notify --no-market-review

# Check code before commit
ruff check . && ruff format . && ty check . && ./test.sh syntax
```

## Notes

- Environment variables: See `.env.example` for all options
- No pytest currently
- Supports A-shares, HK stocks, and US stocks
- Uses multiple data sources for redundancy
