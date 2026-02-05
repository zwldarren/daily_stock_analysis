"""
Pydantic 配置类

提供类型安全、可验证的配置管理
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from pydantic import BaseModel, Field


# 加载 .env 文件（从项目根目录查找）
def _find_project_root() -> Path:
    """查找项目根目录（包含 pyproject.toml 或 .env 的目录）"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".env").exists():
            return parent
    # 默认：返回相对于当前文件的项目根目录
    return current.parents[3]


env_path = _find_project_root() / ".env"
load_dotenv(dotenv_path=env_path)


def parse_list(value: str | None) -> list[str]:
    """解析逗号分隔的列表"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_bool(value: str | None, default: bool = False) -> bool:
    """解析布尔值"""
    if not value:
        return default
    return value.lower() in ("true", "1", "yes", "on")


class Config(BaseModel):
    """系统配置类 - 使用 Pydantic 提供类型验证"""

    # === 自选股配置 ===
    stock_list: list[str] = Field(default_factory=list)

    # === 飞书云文档配置 ===
    feishu_app_id: str | None = None
    feishu_app_secret: str | None = None
    feishu_folder_token: str | None = None

    # === 数据源 API Token ===
    tushare_token: str | None = None

    # === AI 分析配置 ===
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3-flash-preview"
    gemini_model_fallback: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    gemini_request_delay: float = 2.0
    gemini_max_retries: int = 5
    gemini_retry_delay: float = 5.0

    # OpenAI 兼容 API
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7

    # === 搜索引擎配置 ===
    bocha_api_keys: list[str] = Field(default_factory=list)
    tavily_api_keys: list[str] = Field(default_factory=list)
    serpapi_keys: list[str] = Field(default_factory=list)

    # === 通知配置 ===
    wechat_webhook_url: str | None = None
    feishu_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_message_thread_id: str | None = None
    email_sender: str | None = None
    email_password: str | None = None
    email_receivers: list[str] = Field(default_factory=list)
    pushover_user_key: str | None = None
    pushover_api_token: str | None = None
    pushplus_token: str | None = None
    serverchan3_sendkey: str | None = None
    custom_webhook_urls: list[str] = Field(default_factory=list)
    custom_webhook_bearer_token: str | None = None
    discord_bot_token: str | None = None
    discord_main_channel_id: str | None = None
    discord_webhook_url: str | None = None
    astrbot_token: str | None = None
    astrbot_url: str | None = None

    # 消息配置
    single_stock_notify: bool = False
    report_type: str = "simple"
    wechat_msg_type: str = "markdown"
    wechat_max_bytes: int = 4000
    feishu_max_bytes: int = 20000

    # === 数据库配置 ===
    database_path: str = "./data/stock_analysis.db"
    save_context_snapshot: bool = True

    # === 日志配置 ===
    log_dir: str = "./logs"
    log_level: str = "INFO"

    # === 系统配置 ===
    max_workers: int = 3
    debug: bool = False
    http_proxy: str | None = None
    https_proxy: str | None = None

    # === 定时任务配置 ===
    schedule_enabled: bool = False
    schedule_time: str = "18:00"
    market_review_enabled: bool = True
    analysis_delay: int = 0

    # === 实时行情配置 ===
    enable_realtime_quote: bool = True
    enable_chip_distribution: bool = True
    realtime_source_priority: str = "tencent,akshare_sina,efinance,akshare_em"
    realtime_cache_ttl: int = 600
    circuit_breaker_cooldown: int = 300

    # === Discord 配置 ===
    discord_bot_status: str = "A股智能分析 | /help"

    # === 机器人配置 ===
    bot_enabled: bool = True
    bot_command_prefix: str = "/"
    bot_rate_limit_requests: int = 10
    bot_rate_limit_window: int = 60
    bot_admin_users: list[str] = Field(default_factory=list)

    # 飞书机器人
    feishu_verification_token: str | None = None
    feishu_encrypt_key: str | None = None
    feishu_stream_enabled: bool = False

    # 钉钉机器人
    dingtalk_app_key: str | None = None
    dingtalk_app_secret: str | None = None
    dingtalk_stream_enabled: bool = False

    @classmethod
    def from_env(cls) -> Config:
        """从环境变量加载配置"""
        return cls(
            stock_list=parse_list(os.getenv("STOCK_LIST")),
            feishu_app_id=os.getenv("FEISHU_APP_ID"),
            feishu_app_secret=os.getenv("FEISHU_APP_SECRET"),
            feishu_folder_token=os.getenv("FEISHU_FOLDER_TOKEN"),
            tushare_token=os.getenv("TUSHARE_TOKEN"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
            gemini_model_fallback=os.getenv("GEMINI_MODEL_FALLBACK", "gemini-2.5-flash"),
            gemini_temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            gemini_request_delay=float(os.getenv("GEMINI_REQUEST_DELAY", "2.0")),
            gemini_max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "5")),
            gemini_retry_delay=float(os.getenv("GEMINI_RETRY_DELAY", "5.0")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openai_temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            bocha_api_keys=parse_list(os.getenv("BOCHA_API_KEYS")),
            tavily_api_keys=parse_list(os.getenv("TAVILY_API_KEYS")),
            serpapi_keys=parse_list(os.getenv("SERPAPI_API_KEYS")),
            wechat_webhook_url=os.getenv("WECHAT_WEBHOOK_URL"),
            feishu_webhook_url=os.getenv("FEISHU_WEBHOOK_URL"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            telegram_message_thread_id=os.getenv("TELEGRAM_MESSAGE_THREAD_ID"),
            email_sender=os.getenv("EMAIL_SENDER"),
            email_password=os.getenv("EMAIL_PASSWORD"),
            email_receivers=parse_list(os.getenv("EMAIL_RECEIVERS")),
            pushover_user_key=os.getenv("PUSHOVER_USER_KEY"),
            pushover_api_token=os.getenv("PUSHOVER_API_TOKEN"),
            pushplus_token=os.getenv("PUSHPLUS_TOKEN"),
            serverchan3_sendkey=os.getenv("SERVERCHAN3_SENDKEY"),
            custom_webhook_urls=parse_list(os.getenv("CUSTOM_WEBHOOK_URLS")),
            custom_webhook_bearer_token=os.getenv("CUSTOM_WEBHOOK_BEARER_TOKEN"),
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN"),
            discord_main_channel_id=os.getenv("DISCORD_MAIN_CHANNEL_ID"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            astrbot_token=os.getenv("ASTRBOT_TOKEN"),
            astrbot_url=os.getenv("ASTRBOT_URL"),
            single_stock_notify=parse_bool(os.getenv("SINGLE_STOCK_NOTIFY")),
            report_type=os.getenv("REPORT_TYPE", "simple"),
            wechat_msg_type=os.getenv("WECHAT_MSG_TYPE", "markdown"),
            wechat_max_bytes=int(os.getenv("WECHAT_MAX_BYTES", "4000")),
            feishu_max_bytes=int(os.getenv("FEISHU_MAX_BYTES", "20000")),
            database_path=os.getenv("DATABASE_PATH", "./data/stock_analysis.db"),
            save_context_snapshot=parse_bool(os.getenv("SAVE_CONTEXT_SNAPSHOT"), True),
            log_dir=os.getenv("LOG_DIR", "./logs"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_workers=int(os.getenv("MAX_WORKERS", "3")),
            debug=parse_bool(os.getenv("DEBUG")),
            http_proxy=os.getenv("HTTP_PROXY"),
            https_proxy=os.getenv("HTTPS_PROXY"),
            schedule_enabled=parse_bool(os.getenv("SCHEDULE_ENABLED")),
            schedule_time=os.getenv("SCHEDULE_TIME", "18:00"),
            market_review_enabled=parse_bool(os.getenv("MARKET_REVIEW_ENABLED"), True),
            analysis_delay=int(os.getenv("ANALYSIS_DELAY", "0")),
            enable_realtime_quote=parse_bool(os.getenv("ENABLE_REALTIME_QUOTE"), True),
            enable_chip_distribution=parse_bool(os.getenv("ENABLE_CHIP_DISTRIBUTION"), True),
            realtime_source_priority=os.getenv("REALTIME_SOURCE_PRIORITY", "tencent,akshare_sina,efinance,akshare_em"),
            realtime_cache_ttl=int(os.getenv("REALTIME_CACHE_TTL", "600")),
            circuit_breaker_cooldown=int(os.getenv("CIRCUIT_BREAKER_COOLDOWN", "300")),
            discord_bot_status=os.getenv("DISCORD_BOT_STATUS", "A股智能分析 | /help"),
            bot_enabled=parse_bool(os.getenv("BOT_ENABLED"), True),
            bot_command_prefix=os.getenv("BOT_COMMAND_PREFIX", "/"),
            bot_rate_limit_requests=int(os.getenv("BOT_RATE_LIMIT_REQUESTS", "10")),
            bot_rate_limit_window=int(os.getenv("BOT_RATE_LIMIT_WINDOW", "60")),
            bot_admin_users=parse_list(os.getenv("BOT_ADMIN_USERS")),
            feishu_verification_token=os.getenv("FEISHU_VERIFICATION_TOKEN"),
            feishu_encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY"),
            feishu_stream_enabled=parse_bool(os.getenv("FEISHU_STREAM_ENABLED")),
            dingtalk_app_key=os.getenv("DINGTALK_APP_KEY"),
            dingtalk_app_secret=os.getenv("DINGTALK_APP_SECRET"),
            dingtalk_stream_enabled=parse_bool(os.getenv("DINGTALK_STREAM_ENABLED")),
        )

    def get_db_url(self) -> str:
        """获取 SQLAlchemy 数据库连接 URL"""
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.absolute()}"

    def validate_config(self) -> list[str]:
        """验证配置完整性并返回警告信息列表"""
        warnings_list: list[str] = []

        if not self.stock_list:
            warnings_list.append("警告：未配置自选股列表 (STOCK_LIST)")

        if not self.tushare_token:
            warnings_list.append("提示：未配置 Tushare Token，将使用其他数据源")

        if not self.gemini_api_key and not self.openai_api_key:
            warnings_list.append("警告：未配置 Gemini 或 OpenAI API Key，AI 分析功能将不可用")
        elif not self.gemini_api_key:
            warnings_list.append("提示：未配置 Gemini API Key，将使用 OpenAI 兼容 API")

        if not self.bocha_api_keys and not self.tavily_api_keys and not self.serpapi_keys:
            warnings_list.append("提示：未配置搜索引擎 API Key (Bocha/Tavily/SerpAPI)，新闻搜索功能将不可用")

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
            warnings_list.append("提示：未配置通知渠道，将不发送推送通知")

        return warnings_list

    def refresh_stock_list(self) -> None:
        """热读取 STOCK_LIST 环境变量并更新配置"""
        env_path = _find_project_root() / ".env"
        if env_path.exists():
            env_values = dotenv_values(env_path)
            stock_list_str = (env_values.get("STOCK_LIST") or "").strip()
            if stock_list_str:
                self.stock_list = [code.strip() for code in stock_list_str.split(",") if code.strip()]


@lru_cache
def get_config() -> Config:
    """获取配置实例（单例）"""
    return Config.from_env()
