"""Pydantic Settings 配置管理"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_project_root() -> Path:
    """查找项目根目录（包含 pyproject.toml 或 .env 的目录）"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".env").exists():
            return parent
    return current.parents[3]


# 缓存项目根目录，避免重复计算
_PROJECT_ROOT = _find_project_root()


def _parse_comma_list(value: str | None) -> list[str]:
    """解析逗号分隔的列表"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | bool | None) -> bool:
    """解析布尔值"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes")


# 类型别名 - 用于布尔值字段（环境变量中的 true/false 字符串）
EnvBool = Annotated[bool, BeforeValidator(_parse_bool)]


def _validate_temperature(v: float) -> float:
    if not 0 <= v <= 2:
        raise ValueError("Temperature must be between 0 and 2")
    return v


ValidTemperature = Annotated[float, AfterValidator(_validate_temperature)]


# 共用的 model_config
_COMMON_CONFIG = SettingsConfigDict(
    env_file=_PROJECT_ROOT / ".env",
    env_file_encoding="utf-8",
    extra="ignore",
)


# ==========================================
# 嵌套配置类 - 使用 BaseSettings 支持环境变量加载
# ==========================================


class AIConfig(BaseSettings):
    """AI 模型配置"""

    model_config = _COMMON_CONFIG

    # Gemini 配置
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3-flash-preview", validation_alias="GEMINI_MODEL")
    gemini_model_fallback: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL_FALLBACK")
    gemini_temperature: ValidTemperature = Field(default=0.7, validation_alias="GEMINI_TEMPERATURE")
    gemini_request_delay: float = Field(default=2.0, validation_alias="GEMINI_REQUEST_DELAY")
    gemini_max_retries: int = Field(default=5, ge=0, le=10, validation_alias="GEMINI_MAX_RETRIES")
    gemini_retry_delay: float = Field(default=5.0, validation_alias="GEMINI_RETRY_DELAY")

    # OpenAI 配置
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_temperature: ValidTemperature = Field(default=0.7, validation_alias="OPENAI_TEMPERATURE")


class SearchConfig(BaseSettings):
    """搜索引擎配置"""

    model_config = _COMMON_CONFIG

    # 使用 str 存储原始值，通过 computed_field 返回列表
    bocha_api_keys_str: str = Field(default="", validation_alias="BOCHA_API_KEYS")
    tavily_api_keys_str: str = Field(default="", validation_alias="TAVILY_API_KEYS")
    brave_api_keys_str: str = Field(default="", validation_alias="BRAVE_API_KEYS")
    serpapi_keys_str: str = Field(default="", validation_alias="SERPAPI_API_KEYS")

    @computed_field
    @property
    def bocha_api_keys(self) -> list[str]:
        return _parse_comma_list(self.bocha_api_keys_str)

    @computed_field
    @property
    def tavily_api_keys(self) -> list[str]:
        return _parse_comma_list(self.tavily_api_keys_str)

    @computed_field
    @property
    def brave_api_keys(self) -> list[str]:
        return _parse_comma_list(self.brave_api_keys_str)

    @computed_field
    @property
    def serpapi_keys(self) -> list[str]:
        return _parse_comma_list(self.serpapi_keys_str)


class NotificationChannelConfig(BaseSettings):
    """通知渠道配置"""

    model_config = _COMMON_CONFIG

    wechat_webhook_url: str | None = Field(default=None, validation_alias="WECHAT_WEBHOOK_URL")
    feishu_webhook_url: str | None = Field(default=None, validation_alias="FEISHU_WEBHOOK_URL")
    telegram_bot_token: str | None = Field(default=None, validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, validation_alias="TELEGRAM_CHAT_ID")
    telegram_message_thread_id: str | None = Field(default=None, validation_alias="TELEGRAM_MESSAGE_THREAD_ID")
    email_sender: str | None = Field(default=None, validation_alias="EMAIL_SENDER")
    email_password: str | None = Field(default=None, validation_alias="EMAIL_PASSWORD")
    email_receivers_str: str = Field(default="", validation_alias="EMAIL_RECEIVERS")
    pushover_user_key: str | None = Field(default=None, validation_alias="PUSHOVER_USER_KEY")
    pushover_api_token: str | None = Field(default=None, validation_alias="PUSHOVER_API_TOKEN")
    pushplus_token: str | None = Field(default=None, validation_alias="PUSHPLUS_TOKEN")
    serverchan3_sendkey: str | None = Field(default=None, validation_alias="SERVERCHAN3_SENDKEY")
    custom_webhook_urls_str: str = Field(default="", validation_alias="CUSTOM_WEBHOOK_URLS")
    custom_webhook_bearer_token: str | None = Field(default=None, validation_alias="CUSTOM_WEBHOOK_BEARER_TOKEN")
    discord_bot_token: str | None = Field(default=None, validation_alias="DISCORD_BOT_TOKEN")
    discord_main_channel_id: str | None = Field(default=None, validation_alias="DISCORD_MAIN_CHANNEL_ID")
    discord_webhook_url: str | None = Field(default=None, validation_alias="DISCORD_WEBHOOK_URL")
    astrbot_token: str | None = Field(default=None, validation_alias="ASTRBOT_TOKEN")
    astrbot_url: str | None = Field(default=None, validation_alias="ASTRBOT_URL")

    @computed_field
    @property
    def email_receivers(self) -> list[str]:
        return _parse_comma_list(self.email_receivers_str)

    @computed_field
    @property
    def custom_webhook_urls(self) -> list[str]:
        return _parse_comma_list(self.custom_webhook_urls_str)


class NotificationMessageConfig(BaseSettings):
    """通知消息配置"""

    model_config = _COMMON_CONFIG

    single_stock_notify: EnvBool = Field(default=False, validation_alias="SINGLE_STOCK_NOTIFY")
    report_type: str = Field(default="simple", validation_alias="REPORT_TYPE")
    wechat_msg_type: str = Field(default="markdown", validation_alias="WECHAT_MSG_TYPE")
    wechat_max_bytes: int = Field(default=4000, validation_alias="WECHAT_MAX_BYTES")
    feishu_max_bytes: int = Field(default=20000, validation_alias="FEISHU_MAX_BYTES")

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, v: str) -> str:
        if v not in ("simple", "full"):
            raise ValueError("Report type must be 'simple' or 'full'")
        return v


class DatabaseConfig(BaseSettings):
    """数据库配置"""

    model_config = _COMMON_CONFIG

    database_path: str = Field(default="./data/stock_analysis.db", validation_alias="DATABASE_PATH")
    save_context_snapshot: EnvBool = Field(default=True, validation_alias="SAVE_CONTEXT_SNAPSHOT")


class LoggingConfig(BaseSettings):
    """日志配置"""

    model_config = _COMMON_CONFIG

    log_dir: str = Field(default="./logs", validation_alias="LOG_DIR")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class SystemConfig(BaseSettings):
    """系统配置"""

    model_config = _COMMON_CONFIG

    max_workers: int = Field(default=3, ge=1, le=20, validation_alias="MAX_WORKERS")
    debug: EnvBool = Field(default=False, validation_alias="DEBUG")
    http_proxy: str | None = Field(default=None, validation_alias="HTTP_PROXY")
    https_proxy: str | None = Field(default=None, validation_alias="HTTPS_PROXY")


class ScheduleConfig(BaseSettings):
    """定时任务配置"""

    model_config = _COMMON_CONFIG

    schedule_enabled: EnvBool = Field(default=False, validation_alias="SCHEDULE_ENABLED")
    schedule_time: str = Field(default="18:00", validation_alias="SCHEDULE_TIME")
    market_review_enabled: EnvBool = Field(default=True, validation_alias="MARKET_REVIEW_ENABLED")
    analysis_delay: int = Field(default=0, validation_alias="ANALYSIS_DELAY")


class RealtimeQuoteConfig(BaseSettings):
    """实时行情配置"""

    model_config = _COMMON_CONFIG

    enable_realtime_quote: EnvBool = Field(default=True, validation_alias="ENABLE_REALTIME_QUOTE")
    enable_chip_distribution: EnvBool = Field(default=True, validation_alias="ENABLE_CHIP_DISTRIBUTION")
    realtime_source_priority: str = Field(
        default="tencent,akshare_sina,efinance,akshare_em",
        validation_alias="REALTIME_SOURCE_PRIORITY",
    )
    realtime_cache_ttl: int = Field(default=600, validation_alias="REALTIME_CACHE_TTL")
    circuit_breaker_cooldown: int = Field(default=300, validation_alias="CIRCUIT_BREAKER_COOLDOWN")


class DiscordConfig(BaseSettings):
    """Discord 配置"""

    model_config = _COMMON_CONFIG

    discord_bot_status: str = Field(default="A股智能分析 | /help", validation_alias="DISCORD_BOT_STATUS")


class BotConfig(BaseSettings):
    """机器人配置"""

    model_config = _COMMON_CONFIG

    bot_enabled: EnvBool = Field(default=True, validation_alias="BOT_ENABLED")
    bot_command_prefix: str = Field(default="/", validation_alias="BOT_COMMAND_PREFIX")
    bot_rate_limit_requests: int = Field(default=10, validation_alias="BOT_RATE_LIMIT_REQUESTS")
    bot_rate_limit_window: int = Field(default=60, validation_alias="BOT_RATE_LIMIT_WINDOW")
    bot_admin_users_str: str = Field(default="", validation_alias="BOT_ADMIN_USERS")

    @computed_field
    @property
    def bot_admin_users(self) -> list[str]:
        return _parse_comma_list(self.bot_admin_users_str)


class FeishuBotConfig(BaseSettings):
    """飞书机器人配置"""

    model_config = _COMMON_CONFIG

    feishu_verification_token: str | None = Field(default=None, validation_alias="FEISHU_VERIFICATION_TOKEN")
    feishu_encrypt_key: str | None = Field(default=None, validation_alias="FEISHU_ENCRYPT_KEY")
    feishu_stream_enabled: EnvBool = Field(default=False, validation_alias="FEISHU_STREAM_ENABLED")


class DingtalkBotConfig(BaseSettings):
    """钉钉机器人配置"""

    model_config = _COMMON_CONFIG

    dingtalk_app_key: str | None = Field(default=None, validation_alias="DINGTALK_APP_KEY")
    dingtalk_app_secret: str | None = Field(default=None, validation_alias="DINGTALK_APP_SECRET")
    dingtalk_stream_enabled: EnvBool = Field(default=False, validation_alias="DINGTALK_STREAM_ENABLED")


class FeishuDocConfig(BaseSettings):
    """飞书云文档配置"""

    model_config = _COMMON_CONFIG

    feishu_app_id: str | None = Field(default=None, validation_alias="FEISHU_APP_ID")
    feishu_app_secret: str | None = Field(default=None, validation_alias="FEISHU_APP_SECRET")
    feishu_folder_token: str | None = Field(default=None, validation_alias="FEISHU_FOLDER_TOKEN")


class DataSourceConfig(BaseSettings):
    """数据源配置"""

    model_config = _COMMON_CONFIG

    tushare_token: str | None = Field(default=None, validation_alias="TUSHARE_TOKEN")


# ==========================================
# 主配置类
# ==========================================


class Config(BaseSettings):
    """
    系统主配置类

    使用 pydantic-settings 自动从环境变量加载配置
    支持 .env 文件和嵌套配置模型

    嵌套配置类各自独立加载环境变量，无需手动处理
    """

    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        env_parse_none_str="null",
    )

    # 基础配置
    stock_list_str: str = Field(default="", validation_alias="STOCK_LIST")

    # 嵌套配置 - 每个子配置类独立加载环境变量
    ai: AIConfig = Field(default_factory=AIConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    notification_channel: NotificationChannelConfig = Field(default_factory=NotificationChannelConfig)
    notification_message: NotificationMessageConfig = Field(default_factory=NotificationMessageConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    realtime_quote: RealtimeQuoteConfig = Field(default_factory=RealtimeQuoteConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    bot: BotConfig = Field(default_factory=BotConfig)
    feishu_bot: FeishuBotConfig = Field(default_factory=FeishuBotConfig)
    dingtalk_bot: DingtalkBotConfig = Field(default_factory=DingtalkBotConfig)
    feishu_doc: FeishuDocConfig = Field(default_factory=FeishuDocConfig)
    datasource: DataSourceConfig = Field(default_factory=DataSourceConfig)

    @field_validator("stock_list_str", mode="before")
    @classmethod
    def parse_stock_list(cls, v: Any) -> Any:
        """解析股票列表"""
        if isinstance(v, str):
            return v
        return ""

    @computed_field
    @property
    def stock_list(self) -> list[str]:
        return _parse_comma_list(self.stock_list_str)

    # ==========================================
    # 方法
    # ==========================================

    def get_db_url(self) -> str:
        """获取 SQLAlchemy 数据库连接 URL"""
        db_path = Path(self.database.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.absolute()}"

    def validate_config(self) -> list[str]:
        """验证配置完整性并返回警告信息列表"""
        warnings_list: list[str] = []

        if not self.stock_list:
            warnings_list.append("警告：未配置自选股列表 (STOCK_LIST)")

        if not self.datasource.tushare_token:
            warnings_list.append("提示：未配置 Tushare Token，将使用其他数据源")

        if not self.ai.gemini_api_key and not self.ai.openai_api_key:
            warnings_list.append("警告：未配置 Gemini 或 OpenAI API Key，AI 分析功能将不可用")
        elif not self.ai.gemini_api_key:
            warnings_list.append("提示：未配置 Gemini API Key，将使用 OpenAI 兼容 API")

        if (
            not self.search.bocha_api_keys
            and not self.search.tavily_api_keys
            and not self.search.brave_api_keys
            and not self.search.serpapi_keys
        ):
            warnings_list.append("提示：未配置搜索引擎 API Key (Bocha/Tavily/Brave/SerpAPI)，新闻搜索功能将不可用")

        # 检查通知配置
        has_notification = (
            self.notification_channel.wechat_webhook_url
            or self.notification_channel.feishu_webhook_url
            or (self.notification_channel.telegram_bot_token and self.notification_channel.telegram_chat_id)
            or (self.notification_channel.email_sender and self.notification_channel.email_password)
            or (self.notification_channel.pushover_user_key and self.notification_channel.pushover_api_token)
            or self.notification_channel.pushplus_token
            or self.notification_channel.discord_webhook_url
        )
        if not has_notification:
            warnings_list.append("提示：未配置通知渠道，将不发送推送通知")

        return warnings_list

    def refresh_stock_list(self) -> None:
        """热读取 STOCK_LIST 环境变量并更新配置"""
        # 清除缓存并重新实例化
        get_config.cache_clear()


@lru_cache
def get_config() -> Config:
    return Config()


def get_project_root() -> Path:
    """获取项目根目录路径

    Returns:
        项目根目录（包含 pyproject.toml 或 .env 的目录）
    """
    return _PROJECT_ROOT
