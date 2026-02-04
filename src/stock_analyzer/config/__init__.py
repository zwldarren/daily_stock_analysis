"""
配置管理模块

提供类型安全、可验证的配置管理
"""

from pathlib import Path
from typing import Any

from .settings import Settings, get_settings


class Config:
    """
    配置适配器类

    提供与旧代码兼容的接口，底层使用新的 Settings 类
    """

    _instance: Config | None = None

    def __new__(cls) -> Config:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = get_settings()
        return cls._instance

    def __getattr__(self, name: str) -> Any:
        """动态获取属性，优先从新 settings 获取"""
        if hasattr(self._settings, name):
            return getattr(self._settings, name)
        return None

    # Explicitly declare attributes that are set externally to help type checkers
    single_stock_notify: bool = False

    @classmethod
    def get_instance(cls) -> Config:
        """获取配置单例实例"""
        return cls()

    def validate(self) -> list[str]:
        """验证配置完整性"""
        warnings = []

        if not self.stock_list:
            warnings.append("警告：未配置自选股列表 (STOCK_LIST)")

        if not self.tushare_token:
            warnings.append("提示：未配置 Tushare Token，将使用其他数据源")

        if not self.gemini_api_key and not self.openai_api_key:
            warnings.append("警告：未配置 Gemini 或 OpenAI API Key，AI 分析功能将不可用")
        elif not self.gemini_api_key:
            warnings.append("提示：未配置 Gemini API Key，将使用 OpenAI 兼容 API")

        if not self.bocha_api_keys and not self.tavily_api_keys and not self.serpapi_keys:
            warnings.append("提示：未配置搜索引擎 API Key (Bocha/Tavily/SerpAPI)，新闻搜索功能将不可用")

        # 检查通知配置
        has_notification = (
            self.wechat_webhook_url
            or self.feishu_webhook_url
            or (self.telegram_bot_token and self.telegram_chat_id)
            or (self.email_sender and self.email_password)
            or (self.pushover_user_key and self.pushover_api_token)
            or self.pushplus_token
            or self.discord_webhook_url
        )
        if not has_notification:
            warnings.append("提示：未配置通知渠道，将不发送推送通知")

        return warnings

    def get_db_url(self) -> str:
        """获取 SQLAlchemy 数据库连接 URL"""
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.absolute()}"

    def refresh_stock_list(self) -> None:
        """热读取 STOCK_LIST 环境变量并更新配置"""
        from dotenv import dotenv_values

        def find_project_root() -> Path:
            """查找项目根目录"""
            current = Path(__file__).resolve()
            for parent in current.parents:
                if (parent / "pyproject.toml").exists() or (parent / ".env").exists():
                    return parent
            return current.parents[3]

        env_path = find_project_root() / ".env"
        if env_path.exists():
            env_values = dotenv_values(env_path)
            stock_list_str = (env_values.get("STOCK_LIST") or "").strip()
            if stock_list_str:
                self._settings.stock_list = [code.strip() for code in stock_list_str.split(",") if code.strip()]


def get_config() -> Config:
    """获取全局配置实例的快捷方式"""
    return Config.get_instance()


__all__ = ["Config", "Settings", "get_config", "get_settings"]
